import pygame
from math import copysign, sqrt, atan2, sin, cos, degrees, radians
from settings import GRAVITY
from game_data import Map
import shapely.geometry
from enum import Enum, auto
from tile import LineHitbox
from input import Input


class Direction(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()


class Player(pygame.sprite.Sprite):
    """Controls all player functions."""
    def __init__(self, pos: tuple, loaded_obstacle_sprites: pygame.sprite.Group, input_: Input) -> None:
        super().__init__()
        self.image = pygame.image.load('../graphics/player/ball.png').convert_alpha()
        self.rect = self.image.get_rect(midbottom=pos)
        self.radius = self.rect.width / 2
        self.pos = pygame.Vector2(self.rect.center)
        self.offset = pygame.Vector2()  # controlled by camera
        self.original_pos = pos
        self.input = input_

        # general setup
        self.loaded_obstacle_sprites = loaded_obstacle_sprites
        self.display_surf = pygame.display.get_surface()
        self.screen_height = self.display_surf.get_height()
        self.screen_width = self.display_surf.get_width()

        # player attributes
        self.speed = 0.3
        self.default_jumps = 2
        self.shoot_multiplier = 60
        self.mass = 1

        self.velocity = pygame.Vector2()
        self.roll_velocity = pygame.Vector2()
        self.n_jumps = 0
        self.can_jump = False
        self.is_on_ground = False

        self._setup()

    def _setup(self) -> None:
        """General setup and reset functionality."""
        self.velocity = pygame.Vector2()
        self.roll_velocity = pygame.Vector2()

        self.can_jump = True
        self.is_on_ground = False

        self.rotation = 0
        self.rotation_vel = 0

        self.n_jumps = self.default_jumps

    def _move(self, delta_time) -> None:
        """Movement and collision logic."""
        # fall
        self.velocity.y += self.mass * GRAVITY * delta_time

        # move player
        self.pos += self.velocity * delta_time
        self.pos += self.roll_velocity * delta_time
        self.rotation += self.rotation_vel

        # collision logic
        self._collision(delta_time)

        # check for death
        self._death()

        # update sprite position
        self.rect.center = self.pos

    def _death(self) -> None:
        # kill player if off-screen
        if self.offset.y > self.screen_height and (self.offset.x < 0 or self.offset.x > self.screen_width):
            # reset everything
            self.pos.x, self.pos.y = self.original_pos
            self._setup()

    def _get_hitbox(self) -> shapely.geometry.Point:
        return shapely.geometry.Point(self.pos).buffer(self.radius)

    def _collision(self, delta_time: float) -> None:
        """Handle collision logic."""
        prev_pos = self.pos - ((self.velocity + self.roll_velocity) * delta_time)

        player_hitbox = self._get_hitbox()
        trail_hitbox = shapely.geometry.LineString((self.pos, prev_pos))

        collision_sprites = []
        collision_lines = []
        max_score = 0
        max_score_data = ()  # (sprite, line)

        for sprite in self.loaded_obstacle_sprites:
            match sprite.type:
                case Map.platform_collision:
                    line = sprite.line_list[0]
                    if self.velocity.y > 0 and (player_hitbox.intersects(line.hitbox) or trail_hitbox.intersects(line.hitbox)) and prev_pos.y + self.radius < sprite.y:
                        collision_sprites.append(sprite)
                        collision_lines.append(line)
                        score = self._get_collision_score(line.normal_vect)
                        if score > max_score:
                            max_score = score
                            max_score_data = (sprite, line)
                case _:
                    if player_hitbox.intersects(sprite.hitbox) or trail_hitbox.intersects(sprite.hitbox):
                        collision_sprites.append(sprite)
                        for line in sprite.line_list:
                            if player_hitbox.intersects(line.hitbox) or trail_hitbox.intersects(line.hitbox):
                                collision_lines.append(line)
                                score = self._get_collision_score(line.normal_vect)
                                if score > max_score:
                                    max_score = score
                                    max_score_data = (sprite, line)

        if max_score_data:
            # collision logic
            self._exit_tile(prev_pos, collision_sprites)
            self._bounce(delta_time, max_score_data[0], max_score_data[1], collision_lines)
            self._set_rotation_vel(delta_time)
        else:
            # convert roll velocity to actual velocity
            self.velocity += self.roll_velocity
            self.roll_velocity.update()  # set to (0, 0)

    def _set_rotation_vel(self, delta_time) -> None:
        """Calculate rotational velocity from player velocity."""
        velocity = (self.roll_velocity + self.velocity) * delta_time
        self.rotation_vel = copysign(degrees(velocity.magnitude() / self.radius), -velocity.x)

    def _roll(self, delta_time: float, angle: float, is_flipped: bool) -> None:
        """Add roll velocity to player from angle."""
        angle1 = radians(angle)
        angle2 = radians(90 - angle)

        hyp = self.mass * GRAVITY * delta_time * sin(angle1) / 2
        x = hyp * cos(angle2)
        y = hyp * sin(angle2)
        x = x * -1 if is_flipped else x
        self.roll_velocity += x, y

    def _bounce(self, delta_time: float, sprite: pygame.sprite.Sprite, line: LineHitbox, lines: list[LineHitbox]) -> None:
        """Find vector to reflect velocity."""
        roll = False

        # test if on vertex of the line
        if len(lines) == 2:
            for p in line.coords:
                vect = self.pos - p
                if vect.magnitude() < self.radius:
                    # find angle
                    is_flipped = True if vect.x < 0 else False
                    angle = degrees(atan2(-vect.y, abs(vect.x)))

                    # roll
                    roll = True
                    self._roll(delta_time, angle, is_flipped)

        if line.angle == 0 and not roll:
            # stick if flat surface
            self.roll_velocity.update()  # set to (0, 0)
            self.velocity.update()  # set to (0, 0)
            self.is_on_ground = True
            self.reset_jumps()
        else:
            # reflect velocity
            self.velocity = self.velocity.reflect(line.normal_vect)

            # apply bounciness if below threshold
            self.velocity.x -= self.velocity.x * (1 - sprite.bounciness) * abs(line.normal_vect.x)
            self.velocity.y -= self.velocity.y * (1 - sprite.bounciness) * abs(line.normal_vect.y)

    def _get_collision_score(self, normal_vect) -> float:
        """Return score based on angle between velocity and line normal vector."""
        angle = self.velocity.angle_to(normal_vect)
        angle = angle if angle > 0 else angle + 360  # make angle positive
        return 1 - abs(1 - (angle / 180))

    def _exit_tile(self, prev_pos: pygame.Vector2, sprites: list[pygame.sprite.Sprite]) -> None:
        """Move player out of tile sprites."""
        player_hitbox = self._get_hitbox()
        if self.velocity.magnitude() == 0 or not sprites:
            return

        n_steps = 10
        high = prev_pos
        low = self.pos

        step = (high - low) / 2
        self.pos = low + step
        for _ in range(n_steps):
            step /= 2

            collision = False
            for sprite in sprites:
                if player_hitbox.intersects(sprite.hitbox):
                    collision = True

            self.pos = self.pos + step if collision else self.pos - step
            player_hitbox = self._get_hitbox()
        self.pos += step

    def _draw(self) -> None:
        """Draw a rotated sprite to the screen."""
        origin_pos = self.image.get_width() / 2, self.image.get_height() / 2
        image_rect = self.image.get_rect(topleft=(self.offset[0] - origin_pos[0], self.offset[1] - origin_pos[1]))
        offset_center_to_pivot = pygame.Vector2(self.offset[0], self.offset[1]) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(-self.rotation)
        rotated_image_center = (self.offset[0] - rotated_offset.x, self.offset[1] - rotated_offset.y)
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
        self.display_surf.blit(rotated_image, rotated_image_rect)

    def reset_jumps(self) -> None:
        """Reset jumps."""
        self.can_jump = True
        self.n_jumps = self.default_jumps

    def shoot(self) -> None:
        """Shoot player using relative position of mouse from player."""
        self.is_on_ground = False
        self.can_jump = False
        self.n_jumps -= 1

        min_length = 0

        # Set velocity by mouse position
        dx = (self.input.mouse.pos.x - self.offset.x)
        dy = (self.input.mouse.pos.y - self.offset.y)

        if sqrt(dx ** 2 + dy ** 2) > min_length:
            self.velocity = pygame.Vector2(
                copysign(sqrt(abs(dx)), dx),
                copysign(sqrt(abs(dy)), dy)
            ) * self.shoot_multiplier

    def update(self, chunks: int, delta_time: float) -> None:
        """Handle player actions per frame."""
        for _ in range(chunks):
            self._move(delta_time)
        self._draw()
