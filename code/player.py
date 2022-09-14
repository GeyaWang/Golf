import pygame
from math import copysign, sqrt
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

        # player attributes
        self.speed = 0.3
        self.default_jumps = 2
        self.shoot_multiplier = 60

        self.velocity = pygame.Vector2()
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
        if self.loaded_obstacle_sprites.sprites():
            # collision logic for x and y independently
            self.velocity.y += GRAVITY * delta_time
            self.pos += self.velocity.x * delta_time, self.velocity.y * delta_time
            self._collision(delta_time)

            self.rotation += self.rotation_vel
            self.rect.center = self.pos

    def _get_hitbox(self) -> shapely.geometry.Point:
        return shapely.geometry.Point(self.pos).buffer(self.radius)

    def _collision_fix(self, delta_time: float) -> None:
        """Handles if player collides with tile hitbox but not any line hitboxes."""
        # move back and then move forwards with a small stem
        if self.velocity.magnitude() * delta_time > 0.01:
            rel_step = 10
            self._move(-delta_time)
            new_delta_time = delta_time / rel_step
            for _ in range(rel_step):
                self._move(new_delta_time)

    def _collision(self, delta_time: float) -> None:
        """Handle collision logic."""
        player_hitbox = self._get_hitbox()
        collision_sprites = []
        max_score = 0
        max_score_data = ()  # (sprite, line)

        for sprite in self.loaded_obstacle_sprites:
            match sprite.type:
                case Map.platform:
                    sprite_line = sprite.line_list[0]
                    if self.velocity.y > 0 and player_hitbox.intersects(sprite_line.hitbox) and self.pos.y + self.radius - self.velocity.y * delta_time < sprite.y:
                        collision_sprites.append(sprite_line)
                        score = self._get_collision_score(sprite_line.normal_vect)
                        if score > max_score:
                            max_score = score
                            max_score_data = (sprite, sprite_line)
                case _:
                    if player_hitbox.intersects(sprite.hitbox):
                        collision_sprites.append(sprite)
                        for line in sprite.line_list:
                            if player_hitbox.intersects(line.hitbox):
                                score = self._get_collision_score(line.normal_vect)
                                if score > max_score:
                                    max_score = score
                                    max_score_data = (sprite, line)

        if collision_sprites and not max_score_data:
            self._collision_fix(delta_time)

        self._exit_tile(collision_sprites)
        if max_score_data:
            self._bounce(*max_score_data)
        if collision_sprites:
            self.reset_jumps()

    def _bounce(self, sprite: pygame.sprite.Sprite, line: LineHitbox) -> None:
        """Find vector to reflect velocity."""
        # TODO calculate realistic bounce trajectory when at a vertex
        if line.angle == 0:
            # stick if flat surface
            self.velocity.update()  # set to 0, 0
            self.is_on_ground = True
            self.reset_jumps()
        else:
            # reflect velocity
            self.velocity = self.velocity.reflect(line.normal_vect)

            # apply bounciness
            self.velocity.x -= self.velocity.x * sprite.bounciness * abs(line.normal_vect.x)
            self.velocity.y -= self.velocity.y * sprite.bounciness * abs(line.normal_vect.y)

    def _get_collision_score(self, normal_vect):
        """Return score based on angle between velocity and line normal vector."""
        angle = self.velocity.angle_to(normal_vect)
        angle = angle if angle > 0 else angle + 360  # make angle positive
        return 1 - abs(1 - (angle / 180))

    def _exit_tile(self, sprites: list[pygame.sprite.Sprite]) -> None:
        """Move player out of tile sprites."""
        player_hitbox = self._get_hitbox()
        if self.velocity.magnitude() != 0 and sprites:
            step = self.velocity.normalize()
            while True:
                collision = False
                for sprite in sprites:
                    if player_hitbox.intersects(sprite.hitbox):
                        collision = True
                        break
                if not collision:
                    break

                self.pos -= step.x, step.y
                player_hitbox = self._get_hitbox()

    def draw(self) -> None:
        """Draw a rotated sprite to the screen."""
        originPos = self.image.get_size()[0] / 2, self.image.get_size()[1] / 2
        image_rect = self.image.get_rect(topleft=(self.offset[0] - originPos[0], self.offset[1] - originPos[1]))
        offset_center_to_pivot = pygame.Vector2(self.offset[0], self.offset[1]) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(-self.rotation)
        rotated_image_center = (self.offset[0] - rotated_offset.x, self.offset[1] - rotated_offset.y)
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
        self.display_surf.blit(rotated_image, rotated_image_rect)

    def kill(self) -> None:
        """Reset player completely."""
        self.pos.x, self.pos.y = self.original_pos
        self._setup()

    def reset_jumps(self) -> None:
        """Reset jumps."""
        self.can_jump = True
        self.n_jumps = self.default_jumps

    def shoot(self) -> None:
        """Shoot player."""
        self.is_on_ground = False
        self.can_jump = False

        # Set velocity by mouse position
        dx = (self.input.mouse.pos.x - self.offset.x)
        dx = sqrt(abs(dx)) * copysign(1, dx)
        dy = (self.input.mouse.pos.y - self.offset.y)
        dy = sqrt(abs(dy)) * copysign(1, dy)
        self.velocity = pygame.Vector2(dx, dy) * self.shoot_multiplier

    def update(self, delta_time) -> None:
        """Handle player actions per frame."""
        self._move(delta_time)
