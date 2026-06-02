import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

pygame.display.init()
pygame.display.set_mode((1, 1))


class TestConfig(unittest.TestCase):
    def test_constants(self):
        from agentic_game.config import WIDTH, HEIGHT, FPS, GRAVITY, MOVE_SPEED
        self.assertGreater(WIDTH, 0)
        self.assertGreater(HEIGHT, 0)
        self.assertEqual(FPS, 60)
        self.assertGreater(GRAVITY, 0)
        self.assertGreater(MOVE_SPEED, 0)

    def test_colors(self):
        from agentic_game.config import WHITE, BLACK, BG_COLOR
        self.assertEqual(WHITE, (255, 255, 255))
        self.assertEqual(BLACK, (0, 0, 0))
        self.assertEqual(len(BG_COLOR), 3)


class TestParticle(unittest.TestCase):
    def test_create_and_update(self):
        from agentic_game.entities.particle import Particle
        p = Particle(100, 200, (255, 0, 0))
        self.assertTrue(p.update())
        self.assertLess(p.life, 30)

    def test_expires(self):
        from agentic_game.entities.particle import Particle
        p = Particle(0, 0, (255, 255, 255))
        for _ in range(30):
            p.update()
        self.assertFalse(p.update())


class TestPlatform(unittest.TestCase):
    def test_circle_creation(self):
        from agentic_game.entities.platform import Platform
        p = Platform(400, 300, "circle", 40)
        self.assertEqual(p.radius, 40)
        self.assertEqual(p.shape, "circle")
        self.assertTrue(callable(p._noise))

    def test_ellipse_creation(self):
        from agentic_game.entities.platform import Platform
        p = Platform(400, 300, "ellipse", 60, 30, 0.5)
        self.assertEqual(p.shape, "ellipse")
        self.assertEqual(p.rx, 60)
        self.assertEqual(p.ry, 30)
        self.assertTrue(callable(p._noise))

    def test_point_inside_circle(self):
        from agentic_game.entities.platform import Platform
        p = Platform(400, 300, "circle", 40)
        self.assertTrue(p.point_inside(400, 300))
        self.assertTrue(p.point_inside(420, 300))
        self.assertFalse(p.point_inside(500, 300))

    def test_boundary_radius(self):
        from agentic_game.entities.platform import Platform
        p = Platform(400, 300, "circle", 40)
        self.assertAlmostEqual(p.get_boundary_radius(0), 40.0)


class TestPlanetoid(unittest.TestCase):
    def test_falling_creation(self):
        from agentic_game.entities.planetoid import Planetoid
        p = Planetoid(mode="falling")
        self.assertEqual(p.mode, "falling")
        self.assertEqual(p.health, 1)
        self.assertTrue(callable(p._noise))

    def test_moving_creation(self):
        from agentic_game.entities.planetoid import Planetoid
        p = Planetoid(mode="moving")
        self.assertEqual(p.mode, "moving")
        self.assertEqual(p.health, 3)
        self.assertGreater(p.size, 0)
        self.assertTrue(callable(p._noise))

    def test_hit(self):
        from agentic_game.entities.planetoid import Planetoid
        p = Planetoid(mode="falling")
        result = p.hit()
        self.assertIsNotNone(result)
        self.assertTrue(p.done)

    def test_point_inside(self):
        from agentic_game.entities.planetoid import Planetoid
        p = Planetoid(mode="falling")
        self.assertTrue(p.point_inside(p.x, p.y))


class TestPlayer(unittest.TestCase):
    def setUp(self):
        from agentic_game.entities.player import Player
        self.player = Player(
            100, 100, (255, 100, 100),
            {"left": 0, "right": 1, "up": 2, "down": 3, "shoot": 4, "melee": 5},
            "Test",
        )

    def test_initial_state(self):
        self.assertTrue(self.player.alive)
        self.assertEqual(self.player.name, "Test")
        self.assertEqual(self.player.facing, 1)

    def test_die(self):
        result = self.player.die()
        self.assertFalse(self.player.alive)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 20)

    def test_respawn(self):
        self.player.die()
        self.player.respawn()
        self.assertTrue(self.player.alive)

    def test_get_forward_vector(self):
        vx, vy = self.player.get_forward_vector()
        self.assertEqual(vx, 1.0)
        self.assertEqual(vy, 0.0)

    def test_shoot_cooldown(self):
        self.player.last_shot = -1000
        beam = self.player.shoot()
        from agentic_game.entities.projectile import LaserBeam
        self.assertIsInstance(beam, LaserBeam)

    def test_melee_cooldown(self):
        self.player.last_melee = -1000
        swipe = self.player.melee()
        from agentic_game.entities.projectile import LightsaberSwipe
        self.assertIsInstance(swipe, LightsaberSwipe)

    def test_charge_cycle(self):
        self.player.last_shot = -1000
        self.player.start_charge()
        self.assertTrue(self.player.charging)
        self.player.update_charge()
        self.assertNotEqual(self.player.charge_angle, 0)
        beam = self.player.release_charge()
        from agentic_game.entities.projectile import LaserBeam
        self.assertIsInstance(beam, LaserBeam)
        self.assertFalse(self.player.charging)


class TestProjectile(unittest.TestCase):
    def test_laser_beam_creation(self):
        from agentic_game.entities.projectile import LaserBeam
        from agentic_game.entities.player import Player
        player = Player(0, 0, (255, 0, 0), {"shoot": 0}, "P")
        beam = LaserBeam(100, 100, 5, 0, (255, 0, 0), player)
        self.assertFalse(beam.done)
        self.assertIsNone(beam.hit_player)
        self.assertEqual(beam.vx, 5)
        self.assertEqual(beam.vy, 0)

    def test_lightsaber_swipe_creation(self):
        from agentic_game.entities.projectile import LightsaberSwipe
        from agentic_game.entities.player import Player
        player = Player(0, 0, (255, 0, 0), {"melee": 0}, "P")
        swipe = LightsaberSwipe(100, 100, 1, 0, (255, 0, 0), player)
        self.assertFalse(swipe.done)
        self.assertEqual(swipe.lifetime, 10)


class TestEnemy(unittest.TestCase):
    def test_ufo_beam_creation(self):
        from agentic_game.entities.enemy import UFOBeam
        beam = UFOBeam(100, 100, 200, 200)
        self.assertFalse(beam.done)
        self.assertGreater(beam.vx, 0)

    def test_ufo_creation(self):
        from agentic_game.entities.enemy import UFO
        ufo = UFO()
        self.assertFalse(ufo.done)
        self.assertEqual(ufo.state, "entering")
        self.assertGreater(ufo.health, 0)

    def test_ufo_hit(self):
        from agentic_game.entities.enemy import UFO
        ufo = UFO()
        ufo.health = 1
        result = ufo.hit()
        self.assertTrue(ufo.done)
        self.assertIsNotNone(result)

    def test_beam_return_type(self):
        from agentic_game.entities.enemy import UFOBeam
        beam = UFOBeam(100, 100, 50, 50)
        result = beam.update([])
        self.assertIsNone(result)


class TestAsteroidRendering(unittest.TestCase):
    def test_make_noise_func(self):
        from agentic_game.rendering.asteroid import make_noise_func
        noise = make_noise_func(12345)
        self.assertEqual(noise(0), noise(0))
        self.assertNotEqual(noise(0), noise(1))
        self.assertIsInstance(noise(0, 1, 2), int)

    def test_noise_range(self):
        from agentic_game.rendering.asteroid import make_noise_func
        noise = make_noise_func(42)
        for i in range(100):
            val = noise(i)
            self.assertGreaterEqual(val, 0)
            self.assertLess(val, 10000)


if __name__ == "__main__":
    unittest.main()
