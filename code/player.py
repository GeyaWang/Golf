import pygame
from math import pi, copysign, sqrt
from settings import DELTA_TIME, GRAVITY
import shapely.geometry


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, obstacle_sprites):
        super().__init__()

        self.image = pygame.image.load('../graphics/player/ball.png').convert_alpha()
        self.rect = self.image.get_rect(midbottom=pos)
        self.radius = self.rect.width / 2
        self.x, self.y = self.rect.center
        self.velocity = pygame.Vector2()

        self.display_surf = pygame.display.get_surface()
        self.obstacle_sprites = obstacle_sprites

        self.speed = 0.3

        self.rotation = 0
        self.rotation_vel = 0

    def _move(self):
        # collision logic for x and y independently
        self.velocity.y += GRAVITY * DELTA_TIME
        self.y += self.velocity.y
        self.rect.centery = self.y
        self._collision('vertical')

        self.x += self.velocity.x
        self.rect.centerx = self.x
        self._collision('horizontal')

        self.rect.center = self.x, self.y

    def _collision(self, direction):
        if direction == 'horizontal':
            player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

            min_score = 99
            min_score_data = ()  # (sprite, line)
            for sprite in self.obstacle_sprites:
                if player_hitbox.intersects(sprite.hitbox):

                    self._exit_tile(sprite, direction)

                    for line in sprite.hitbox_list:
                        if player_hitbox.intersects(line.hitbox):
                            # find score based on how much the angle of velocity opposes the line (smaller = better)
                            score = 1 - abs(self.velocity.angle_to(line.normal_vect)) / 180
                            if score < min_score:
                                min_score = score
                                min_score_data = (sprite, line)

            # collision logic with most suitable line object
            if min_score_data:
                self._bounce(*min_score_data)

        else:  # vertical
            player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

            min_score = 999
            min_score_data = ()  # (sprite, line)
            min_angle = 999  # find minimum angle for roll logic
            for sprite in self.obstacle_sprites:
                if player_hitbox.intersects(sprite.hitbox):

                    self._exit_tile(sprite, direction)

                    for line in sprite.hitbox_list:
                        if player_hitbox.intersects(line.hitbox):
                            # find score based on how much the angle of velocity opposes the line (smaller = better)
                            score = abs(1 + self.velocity.angle_to(line.normal_vect) / 180)
                            if score < min_score:
                                min_score = score
                                min_score_data = (sprite, line)

            # collision logic with most suitable line object
            if min_score_data:
                self._bounce(*min_score_data)

    def _exit_tile(self, sprite, direction):
        # move player out of tile

        if direction == 'horizontal':
            player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)
            if self.velocity.magnitude() != 0:
                vel = self.velocity.normalize()

                i = 0  # iteration limit
                while player_hitbox.intersects(sprite.hitbox):
                    i += 1
                    if i > 1000:
                        break
                    self.x -= vel.x
                    player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

        else:  # vertical
            player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)
            if self.velocity.magnitude() != 0:
                vel = self.velocity.normalize()

                i = 0  # iteration limit
                while player_hitbox.intersects(sprite.hitbox):
                    i += 1
                    if i > 1000:
                        break
                    self.y -= vel.y
                    player_hitbox = shapely.geometry.Point(self.x, self.y).buffer(self.radius)

    def _bounce(self, sprite, line):
        # stick if flat platform
        if line.angle == 0:
            self.velocity.update(0, 0)
        else:
            # bounce
            self.velocity = self.velocity.reflect(line.normal_vect)

            # apply bounciness
            self.velocity.x *= 1 - (1 - sprite.bounciness) * abs(line.normal_vect.x)
            self.velocity.y *= 1 - (1 - sprite.bounciness) * abs(line.normal_vect.x)

    def _get_rotation_vel(self):
        velocity = self.velocity.magnitude()
        if abs(velocity) > 1:
            self.rotation_vel = -(180 * velocity) / (pi * self.radius)
        else:
            self.rotation_vel = 0

    def _input(self):
        pass

    def _draw(self):
        # Rotate image and display it
        pos = self.rect.center
        originPos = self.image.get_size()[0] / 2, self.image.get_size()[1] / 2

        image_rect = self.image.get_rect(topleft=(pos[0] - originPos[0], pos[1] - originPos[1]))
        offset_center_to_pivot = pygame.Vector2(pos) - image_rect.center
        rotated_offset = offset_center_to_pivot.rotate(-self.rotation)
        rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)
        rotated_image = pygame.transform.rotate(self.image, self.rotation)
        rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
        self.display_surf.blit(rotated_image, rotated_image_rect)

    def shoot(self):
        # Set velocity by mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = (mouse_x - self.rect.centerx)
        dx = sqrt(abs(dx)) * copysign(1, dx)
        dy = (mouse_y - self.rect.centery)
        dy = sqrt(abs(dy)) * copysign(1, dy)
        self.velocity = pygame.Vector2(dx, dy)

    def update(self):
        self._draw()
        self._move()
