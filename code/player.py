import pygame
from math import pi, copysign, sqrt
from settings import DELTA_TIME, GRAVITY
from game_data import Map
import shapely.geometry
from enum import Enum
from tile import Tile, LineHitbox


class Direction(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, obstacle_sprites, visible_sprites) -> None:
        super().__init__()

        self.image = pygame.image.load('../graphics/player/ball.png').convert_alpha()
        self.rect = self.image.get_rect(midbottom=pos)
        self.radius = self.rect.width / 2
        self.x, self.y = self.rect.center
        self.offset = pygame.Vector2()  # controlled by camera
        self.original_pos = pos

        self.obstacle_sprites = obstacle_sprites
        self.visible_sprite = visible_sprites
        self.display_surf = pygame.display.get_surface()

        self.speed = 0.3
        self.default_jumps = 2

        self.velocity = pygame.Vector2()
        self.n_jumps = 0
        self.can_jump = False

        self._setup()

    def _setup(self) -> None:
        """General setup and reset functionality."""
        self.velocity = pygame.Vector2()
        self.roll_velocity = pygame.Vector2()
        self.can_jump = True
        self.i_frames = True
        self.i_frame_count = 0
        self.i_frame_total_count = 0
        self.rotation = 0
        self.rotation_vel = 0
        self.n_jumps = self.default_jumps

    def _move(self) -> None:
        """Movement and collision logic."""
        # collision logic for x and y independently
        self.velocity.y += GRAVITY * DELTA_TIME
        self.y += self.velocity.y
        self.y += self.roll_velocity.y
        self._collision(Direction.VERTICAL)

        self.x += self.velocity.x
        self.x += self.roll_velocity.x
        self._collision(Direction.HORIZONTAL)

        self.rotation += self.rotation_vel
        self.rect.center = self.x, self.y

    def _collision(self, direction: Direction) -> None:
        """Handle collision logic."""
        player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

        min_score = 999  # float
        min_score_data = ()  # tuple[Tile, LineHitbox]

        for sprite in self.obstacle_sprites:
            match sprite.type:
                case Map.platform:
                    if self.velocity.y > 0 and player_hitbox.intersects(sprite.line_list[0].hitbox) and direction == Direction.VERTICAL:
                        self._exit_tile(sprite.line_list[0], direction)
                        min_score, min_score_data = self._get_collision_score(min_score, min_score_data, sprite, sprite.line_list[0])
                case _:
                    if player_hitbox.intersects(sprite.hitbox):
                        self._exit_tile(sprite, direction)
                        for line in sprite.line_list:
                            if player_hitbox.intersects(line.hitbox):
                                min_score, min_score_data = self._get_collision_score(min_score, min_score_data, sprite, line)

        # collision logic with most suitable line object
        if min_score_data:
            self._roll(min_score_data[1])
            self._bounce(*min_score_data)
            self._set_rotation_vel()

    def _roll(self, line):
        """Calculate rolling logic."""
        # find difference in y
        (x1, y1), (x2, y2) = line.coords
        if x1 == x2:
            # exit
            return
        m1 = 0.00001 if y1 == y2 else (y1 - y2) / (x1 - x2)  # avoid division by zero
        m2 = -(1 / m1)
        y = (-m1 * self.y - m1 * m2 * (x2 - self.x) + m2 * y2) / (m2 - m1)
        diff_y = self.y - y + self.radius

        square_diff = self.radius ** 2 - diff_y ** 2
        if square_diff < 0:
            # exit
            return
        diff_x = (sqrt(square_diff) - self.radius) * copysign(1, min(x1 - self.x, x2 - self.x))
        if abs(diff_y) > 0.1:
            self.roll_velocity.x += diff_x
        else:
            self.roll_velocity.update()

    def _get_collision_score(self, min_score: float, min_score_data: tuple[Tile, LineHitbox], sprite, line) -> tuple[float, tuple[Tile, LineHitbox]]:
        """Calculate score based on how much the angle of velocity opposes the line."""
        score = abs(1 - abs(self.velocity.angle_to(line.normal_vect)) / 180)  # smaller is better
        if min_score is None or score < min_score:
            min_score = score
            min_score_data = (sprite, line)
        return min_score, min_score_data

    def _exit_tile(self, sprite: Tile, direction: Direction) -> None:
        """Logic to move player backwards outside tile"""
        if direction == Direction.HORIZONTAL:
            player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)
            if self.velocity.magnitude() != 0:
                step = copysign(1, self.velocity.x) * 0.1
                for x in range(100):  # iteration limit
                    if not player_hitbox.intersects(sprite.hitbox):
                        break
                    self.x -= step
                    player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

        else:  # vertical
            player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)
            if self.velocity.magnitude() != 0:
                step = copysign(1, self.velocity.y) * 0.1
                for x in range(100):  # iteration limit
                    if not player_hitbox.intersects(sprite.hitbox):
                        break
                    self.y -= step
                    player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

    def _bounce(self, sprite: Tile, line: LineHitbox) -> None:
        """Calculate bouncing logic."""
        self.can_jump = True

        # stick if flat platform
        if line.angle == 0:
            self.velocity.update()
            self.reset_jumps()
        else:
            # bounce
            self.velocity = self.velocity.reflect(line.normal_vect)

            # apply bounciness
            # find the magnitude of the vector that is a component of the velocity and goes along the normal vector of the line
            magnitude = self.velocity.dot(line.normal_vect) / line.normal_vect.magnitude()
            if magnitude > 1:  # threshold
                self.velocity.x *= 1 - (1 - sprite.bounciness) * abs(line.normal_vect.x)
                self.velocity.y *= 1 - (1 - sprite.bounciness) * abs(line.normal_vect.x)
            else:
                self.velocity.update()

    def _set_rotation_vel(self) -> None:
        """Calculate rotational velocity from player velocity."""
        velocity = self.velocity.magnitude() + self.roll_velocity.magnitude()
        if abs(velocity) > 1:
            self.rotation_vel = ((180 * velocity) / (pi * self.radius)) * copysign(1, self.velocity.x + self.roll_velocity.x)
        else:
            self.rotation_vel = 0

    def _draw_player(self) -> None:
        """Draw a rotated sprite to the screen."""
        originPos = self.image.get_size()[0] / 2, self.image.get_size()[1] / 2
        image_rect = self.image.get_rect(topleft=(self.offset[0] - originPos[0], self.offset[1] - originPos[1]))
        offset_center_to_pivot = pygame.Vector2(self.offset[0], self.offset[1]) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(-self.rotation)
        rotated_image_center = (self.offset[0] - rotated_offset.x, self.offset[1] - rotated_offset.y)
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
        self.display_surf.blit(rotated_image, rotated_image_rect)

    def _draw(self) -> None:
        """Logic to test if player should be drawn."""
        if not self.i_frames or self.i_frame_count < 10:
            self._draw_player()
        elif self.i_frame_count >= 20:
            self.i_frame_count = 0

        if self.i_frames:
            self.i_frame_total_count += 1
            self.i_frame_count += 1
        if self.i_frame_total_count >= 100:
            self.i_frame_total_count = 0
            self.i_frame_count = 0
            self.i_frames = False

    def kill(self) -> None:
        """Reset player."""
        self.x, self.y = self.original_pos
        self._setup()

    def reset_jumps(self) -> None:
        """Reset jumps."""
        self.n_jumps = self.default_jumps

    def shoot(self) -> None:
        """Shoot player."""
        self.can_jump = False

        # Set velocity by mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = (mouse_x - self.offset.x)
        dx = sqrt(abs(dx)) * copysign(1, dx)
        dy = (mouse_y - self.offset.y)
        dy = sqrt(abs(dy)) * copysign(1, dy)
        self.velocity = pygame.Vector2(dx, dy)

    def update(self) -> None:
        """Handle player actions per frame."""
        self._move()
        self._draw()
