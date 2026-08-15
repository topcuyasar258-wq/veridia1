import threading
import unittest

from playwright.sync_api import sync_playwright

import server


class SiteMotionBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        server.clear_rate_limit_state()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.AppHandler)
        cls.base_url = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        cls.server_thread = threading.Thread(
            target=cls.httpd.serve_forever,
            daemon=True,
        )
        cls.server_thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join(timeout=5)
        server.clear_rate_limit_state()

    def test_representative_pages_initialize_without_browser_errors(self) -> None:
        routes = (
            "/",
            "/blog",
            "/blog/instagram-algoritmasi-2026",
            "/hizmetler/",
            "/seo/",
            "/sektorler/",
            "/calismalarimiz",
            "/hizli-teklif",
            "/gizlilik-politikasi",
        )
        context = self.browser.new_context()
        try:
            for route in routes:
                with self.subTest(route=route):
                    page = context.new_page()
                    errors: list[str] = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    response = page.goto(
                        f"{self.base_url}{route}",
                        wait_until="domcontentloaded",
                    )
                    page.wait_for_selector("html.v-motion-enabled")

                    self.assertIsNotNone(response)
                    self.assertEqual(200, response.status)
                    self.assertTrue(page.locator("h1").first.is_visible())
                    self.assertEqual(
                        0,
                        page.locator(
                            ".reveal .v-motion-reveal, "
                            ".v-motion-reveal .reveal:not(.v-motion-passive)"
                        ).count(),
                    )
                    self.assertEqual([], errors)
                    page.close()
        finally:
            context.close()

    def test_homepage_has_visible_signature_motion_density(self) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector("html.v-motion-enabled")
            counts = page.evaluate(
                """({
                    reveal: document.querySelectorAll('.v-motion-reveal').length,
                    cards: document.querySelectorAll('.v-motion-card').length,
                    ctas: document.querySelectorAll('.v-motion-cta').length,
                    legacyAdopted: document.querySelectorAll(
                        '.reveal.v-motion-reveal'
                    ).length
                })"""
            )

            self.assertGreaterEqual(counts["reveal"], 24)
            self.assertGreaterEqual(counts["cards"], 8)
            self.assertGreaterEqual(counts["ctas"], 4)
            self.assertGreaterEqual(counts["legacyAdopted"], 20)
        finally:
            context.close()

    def test_home_motion_preserves_existing_decorative_positioning(self) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector("html.v-motion-enabled")

            for selector in (".hero-bg", ".hero-grid", ".hero-number"):
                with self.subTest(selector=selector):
                    self.assertEqual(
                        "absolute",
                        page.locator(selector).evaluate(
                            "node => getComputedStyle(node).position"
                        ),
                    )
        finally:
            context.close()

    def test_home_hero_scramble_resolves_without_changing_accessible_copy(
        self,
    ) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            hero_title = page.locator(".hero-title")
            globe = page.locator("#hero > .v-motion-globe")
            expected_copy = (
                "Web Sitesi, SEO ve Reklamla "
                "Daha Fazla Müşteri Adayı Kazanın"
            )
            expected_text_content = expected_copy.replace("Reklamla ", "Reklamla")

            page.wait_for_selector(".hero-title.v-scramble-ready")
            self.assertEqual(1, globe.count())
            self.assertEqual("true", globe.get_attribute("aria-hidden"))
            self.assertEqual(expected_copy, hero_title.get_attribute("aria-label"))
            self.assertGreater(
                hero_title.locator(".v-scramble-char").count(),
                40,
            )

            page.wait_for_selector(
                ".hero-title.is-scramble-complete",
                timeout=3_000,
            )
            settled_copy = hero_title.evaluate(
                """
                (node) => ({
                  innerText: node.innerText.replace(/\\s+/g, ' ').trim(),
                  textContent: node.textContent.replace(/\\s+/g, ' ').trim()
                })
                """
            )

            self.assertEqual(0, hero_title.locator(".v-scramble-char").count())
            self.assertEqual(expected_copy, settled_copy["innerText"])
            self.assertEqual(expected_text_content, settled_copy["textContent"])
            self.assertIsNone(hero_title.get_attribute("aria-label"))
        finally:
            context.close()

    def test_blog_cards_keep_their_native_filter_and_hover_transitions(
        self,
    ) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/blog", wait_until="domcontentloaded")
            card = page.locator(".blog-card").first
            page.wait_for_selector(".blog-card.v-motion-card")

            transition_duration = card.evaluate(
                "node => getComputedStyle(node).transitionDuration"
            )
            self.assertNotIn("0.78s", transition_duration)

            card.hover()
            self.assertIn(
                card.evaluate("node => getComputedStyle(node).translate"),
                ("none", "0px"),
            )
        finally:
            context.close()

    def test_below_fold_scramble_is_prepared_only_when_it_enters_view(
        self,
    ) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            manifesto = page.locator(".reference-manifesto h2")
            page.wait_for_selector(".hero-title.v-scramble-ready")

            self.assertEqual(0, manifesto.locator(".v-scramble-char").count())
            self.assertFalse(
                manifesto.evaluate(
                    "node => node.classList.contains('v-scramble-ready')"
                )
            )

            manifesto.scroll_into_view_if_needed()
            page.wait_for_selector(
                ".reference-manifesto h2.v-scramble-ready",
                timeout=3_000,
            )
            self.assertGreater(
                manifesto.locator(".v-scramble-char").count(),
                40,
            )
        finally:
            context.close()

    def test_home_scroll_story_changes_copy_and_releases_the_next_section(
        self,
    ) -> None:
        context = self.browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            track = page.locator(".v-scroll-track")
            hero = page.locator("#hero.v-scroll-story")
            page.wait_for_selector(".v-scroll-track #hero.v-scroll-story")
            page.evaluate(
                "document.documentElement.style.scrollBehavior = 'auto'"
            )

            geometry = track.evaluate(
                """
                node => ({
                  height: node.getBoundingClientRect().height,
                  position: getComputedStyle(
                    node.querySelector('#hero')
                  ).position,
                  viewport: innerHeight,
                  canvas: (() => {
                    const canvas = node.querySelector('.v-motion-globe');
                    const bounds = canvas.getBoundingClientRect();
                    return {
                      height: bounds.height,
                      pixels: canvas.width * canvas.height
                    };
                  })()
                })
                """
            )
            self.assertGreater(geometry["height"], geometry["viewport"] * 3)
            self.assertEqual("sticky", geometry["position"])
            self.assertLessEqual(
                geometry["canvas"]["height"],
                geometry["viewport"],
            )
            self.assertLessEqual(geometry["canvas"]["pixels"], 2_400_000)

            def scroll_to_progress(progress: float) -> None:
                page.evaluate(
                    """
                    ({ progress }) => {
                      const track = document.querySelector('.v-scroll-track');
                      const hero = track.querySelector('#hero');
                      const stickyTop =
                        parseFloat(getComputedStyle(hero).top) || 0;
                      const travel =
                        track.offsetHeight - hero.getBoundingClientRect().height;
                      window.scrollTo(
                        0,
                        track.offsetTop - stickyTop + travel * progress
                      );
                    }
                    """,
                    {"progress": progress},
                )
                page.wait_for_timeout(120)

            scroll_to_progress(0)
            self.assertEqual("0", hero.get_attribute("data-v-story-scene"))
            self.assertEqual(
                "false",
                hero.locator(".hero-content").get_attribute("aria-hidden"),
            )
            self.assertFalse(
                hero.locator(".hero-content").evaluate("node => node.inert")
            )
            hero.locator(".hero-cta a").first.focus()
            expected_story_scroll_y = track.evaluate(
                """
                node => {
                  const hero = node.querySelector('#hero');
                  const stickyTop =
                    parseFloat(getComputedStyle(hero).top) || 0;
                  const travel =
                    node.offsetHeight - hero.getBoundingClientRect().height;
                  return node.offsetTop - stickyTop + travel * 0.44;
                }
                """
            )

            scroll_to_progress(0.44)
            self.assertEqual("1", hero.get_attribute("data-v-story-scene"))
            self.assertEqual(
                "false",
                hero.locator('[data-v-story-scene="1"]').get_attribute(
                    "aria-hidden"
                ),
            )
            self.assertTrue(
                hero.locator(".hero-content").evaluate("node => node.inert")
            )
            self.assertEqual(
                1,
                hero.locator(
                    '.hero-content[aria-hidden="false"], '
                    '.v-scroll-scene[aria-hidden="false"]'
                ).count(),
            )
            self.assertGreater(
                hero.evaluate(
                    "node => Number(node.style.getPropertyValue('--v-story-focus'))"
                ),
                0.85,
            )
            self.assertEqual(
                "1",
                page.locator(":focus").get_attribute("data-v-story-scene"),
            )
            self.assertAlmostEqual(
                page.evaluate("window.scrollY"),
                expected_story_scroll_y,
                delta=2,
            )

            scroll_to_progress(0.70)
            self.assertEqual("2", hero.get_attribute("data-v-story-scene"))
            self.assertEqual(
                "false",
                hero.locator('[data-v-story-scene="2"]').get_attribute(
                    "aria-hidden"
                ),
            )
            self.assertEqual(
                1,
                hero.locator(
                    '.hero-content[aria-hidden="false"], '
                    '.v-scroll-scene[aria-hidden="false"]'
                ).count(),
            )
            self.assertEqual(
                "02",
                hero.locator(".v-scroll-index li.is-active").inner_text(),
            )

            scroll_to_progress(0.90)
            fracture = hero.evaluate(
                "node => Number(node.style.getPropertyValue('--v-story-fracture'))"
            )
            self.assertGreater(fracture, 0)
            self.assertLess(fracture, 1)

            scroll_to_progress(1)
            self.assertEqual("-1", hero.get_attribute("data-v-story-scene"))
            self.assertEqual(
                0,
                hero.locator('.v-scroll-scene[aria-hidden="false"]').count(),
            )
            self.assertEqual(
                "true",
                hero.locator(".hero-content").get_attribute("aria-hidden"),
            )

            scroll_to_progress(0.70)
            hero.locator(
                '.v-scroll-scene[data-v-story-scene="2"]'
            ).focus()
            scroll_to_progress(0.05)
            self.assertEqual("0", hero.get_attribute("data-v-story-scene"))
            self.assertEqual(
                0,
                hero.evaluate(
                    "node => Number(node.style.getPropertyValue('--v-story-fracture'))"
                ),
            )
            self.assertEqual(
                "A",
                page.locator(":focus").evaluate("node => node.tagName"),
            )
            self.assertIsNone(
                hero.locator(".hero-cta a").first.get_attribute("tabindex")
            )

            page.evaluate(
                """
                () => {
                  const track = document.querySelector('.v-scroll-track');
                  window.scrollTo(
                    0,
                    track.offsetTop + track.offsetHeight - innerHeight + 24
                  );
                }
                """
            )
            page.wait_for_timeout(120)
            self.assertLess(
                page.locator(".reference-trust").evaluate(
                    "node => node.getBoundingClientRect().top"
                ),
                900,
            )
        finally:
            context.close()

    def test_mobile_scroll_story_has_no_overflow_and_releases_normally(
        self,
    ) -> None:
        context = self.browser.new_context(
            viewport={"width": 390, "height": 844}
        )
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector(".v-scroll-track #hero.v-scroll-story")
            page.evaluate(
                "document.documentElement.style.scrollBehavior = 'auto'"
            )
            metrics = page.evaluate(
                """
                () => {
                  const track = document.querySelector('.v-scroll-track');
                  window.scrollTo(
                    0,
                    track.offsetTop + track.offsetHeight - innerHeight + 32
                  );
                  return {
                    overflow:
                      document.documentElement.scrollWidth -
                      document.documentElement.clientWidth,
                    trackHeight: track.getBoundingClientRect().height,
                    viewport: innerHeight
                  };
                }
                """
            )
            page.wait_for_timeout(120)

            self.assertLessEqual(metrics["overflow"], 1)
            self.assertGreater(metrics["trackHeight"], metrics["viewport"] * 3)
            self.assertLess(
                page.locator(".reference-trust").evaluate(
                    "node => node.getBoundingClientRect().top"
                ),
                844,
            )
        finally:
            context.close()

    def test_mobile_light_story_stays_inside_the_visible_area(self) -> None:
        context = self.browser.new_context(
            viewport={"width": 390, "height": 844},
            has_touch=True,
            is_mobile=True,
        )
        context.add_init_script(
            "localStorage.setItem('veridia-theme', 'light')"
        )
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector(".v-scroll-track #hero.v-scroll-story")
            page.evaluate(
                "document.documentElement.style.scrollBehavior = 'auto'"
            )
            page.evaluate(
                """
                () => {
                  const track = document.querySelector('.v-scroll-track');
                  const hero = track.querySelector('#hero');
                  const stickyTop =
                    parseFloat(getComputedStyle(hero).top) || 0;
                  const travel =
                    track.offsetHeight - hero.getBoundingClientRect().height;
                  window.scrollTo(
                    0,
                    track.offsetTop - stickyTop + travel * 0.44
                  );
                }
                """
            )
            page.wait_for_timeout(120)

            geometry = page.evaluate(
                """
                () => {
                  const rect = (node) => {
                    const bounds = node.getBoundingClientRect();
                    return { top: bounds.top, bottom: bounds.bottom };
                  };
                  const hero = document.querySelector('#hero');
                  const scene = hero.querySelector(
                    '.v-scroll-scene[aria-hidden="false"]'
                  );
                  return {
                    viewportBottom: innerHeight,
                    hero: rect(hero),
                    scene: rect(scene)
                  };
                }
                """
            )

            self.assertEqual(
                "light",
                page.locator("html").get_attribute("data-theme"),
            )
            self.assertLessEqual(
                geometry["hero"]["bottom"],
                geometry["viewportBottom"] + 1,
            )
            self.assertLessEqual(
                geometry["scene"]["bottom"],
                geometry["viewportBottom"] - 88,
            )
        finally:
            context.close()

    def test_short_landscape_story_keeps_intro_and_cta_inside_the_hero(
        self,
    ) -> None:
        context = self.browser.new_context(
            viewport={"width": 667, "height": 375}
        )
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector('html[data-v-story="static"]')
            bounds = page.evaluate(
                """
                () => {
                  const hero = document.querySelector('#hero');
                  const label = hero.querySelector('.hero-label');
                  const cta = hero.querySelector('.hero-cta');
                  const rect = (node) => {
                    const bounds = node.getBoundingClientRect();
                    return { top: bounds.top, bottom: bounds.bottom };
                  };
                  return {
                    hero: rect(hero),
                    label: rect(label),
                    cta: rect(cta)
                  };
                }
                """
            )

            self.assertGreaterEqual(
                bounds["label"]["top"],
                bounds["hero"]["top"] - 1,
            )
            self.assertLessEqual(
                bounds["cta"]["bottom"],
                bounds["hero"]["bottom"] + 1,
            )
            self.assertTrue(page.locator(".hero-cta a").first.is_visible())
            self.assertEqual(0, page.locator(".v-scroll-track").count())
            self.assertTrue(page.locator(".v-story-static").is_visible())
        finally:
            context.close()

    def test_reduced_motion_skips_homepage_canvas_and_scramble(self) -> None:
        context = self.browser.new_context(reduced_motion="reduce")
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector('html[data-v-motion="static"]')

            self.assertEqual(0, page.locator(".v-motion-globe").count())
            self.assertEqual(0, page.locator(".v-scramble-char").count())
            self.assertEqual(0, page.locator(".v-scroll-track").count())
            self.assertTrue(page.locator(".hero-title").is_visible())
            self.assertTrue(page.locator(".v-story-static").is_visible())
            self.assertEqual(
                2,
                page.locator(".v-story-static-grid h2").count(),
            )
            self.assertIn(
                "Doğru müşterinin karşısına çıkın.",
                page.locator(".v-story-static").inner_text(),
            )
        finally:
            context.close()

    def test_reduced_motion_keeps_reveal_content_visible(self) -> None:
        context = self.browser.new_context(reduced_motion="reduce")
        page = context.new_page()
        try:
            page.goto(
                f"{self.base_url}/hizmetler/",
                wait_until="domcontentloaded",
            )
            page.wait_for_selector('html[data-v-motion="static"]')
            reveal = page.locator(".v-motion-reveal").first

            self.assertGreater(page.locator(".v-motion-reveal").count(), 0)
            self.assertTrue(reveal.is_visible())
            self.assertEqual("1", reveal.evaluate("node => getComputedStyle(node).opacity"))
        finally:
            context.close()

    def test_live_reduced_motion_replaces_story_with_static_copy(self) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector(".v-scroll-track #hero.v-scroll-story")
            page.evaluate(
                """
                () => {
                  const track = document.querySelector('.v-scroll-track');
                  const hero = track.querySelector('#hero');
                  const stickyTop =
                    parseFloat(getComputedStyle(hero).top) || 0;
                  const travel =
                    track.offsetHeight - hero.getBoundingClientRect().height;
                  document.documentElement.style.scrollBehavior = 'auto';
                  scrollTo(
                    0,
                    track.offsetTop - stickyTop + travel * 0.44
                  );
                }
                """
            )
            page.wait_for_timeout(120)
            page.locator(
                '.v-scroll-scene[data-v-story-scene="1"]'
            ).focus()

            page.emulate_media(reduced_motion="reduce")
            page.wait_for_selector('html[data-v-story="static"]')

            self.assertEqual(0, page.locator(".v-scroll-track").count())
            self.assertTrue(page.locator(".v-story-static").is_visible())
            self.assertEqual(
                2,
                page.locator(".v-story-static-grid article").count(),
            )
            self.assertIsNone(
                page.locator(".hero-content").get_attribute("aria-hidden")
            )
            self.assertFalse(
                page.locator(".hero-content").evaluate("node => node.inert")
            )
            self.assertEqual(
                "1",
                page.locator(":focus").get_attribute(
                    "data-v-static-story-scene"
                ),
            )
        finally:
            context.close()

    def test_live_save_data_replaces_story_with_static_copy(self) -> None:
        context = self.browser.new_context()
        context.add_init_script(
            """
            (() => {
              const listeners = new Set();
              const connection = {
                saveData: false,
                addEventListener(type, listener) {
                  if (type === 'change') listeners.add(listener);
                },
                removeEventListener(type, listener) {
                  if (type === 'change') listeners.delete(listener);
                }
              };
              Object.defineProperty(navigator, 'connection', {
                configurable: true,
                value: connection
              });
              window.__enableSaveData = () => {
                connection.saveData = true;
                listeners.forEach((listener) => listener());
              };
            })();
            """
        )
        page = context.new_page()
        try:
            page.goto(f"{self.base_url}/", wait_until="domcontentloaded")
            page.wait_for_selector(".v-scroll-track #hero.v-scroll-story")
            hero_cta = page.locator(".hero-cta a").first
            hero_cta.focus()

            page.evaluate("window.__enableSaveData()")
            page.wait_for_selector('html[data-v-story="static"]')

            self.assertEqual(0, page.locator(".v-scroll-track").count())
            self.assertTrue(page.locator(".v-story-static").is_visible())
            self.assertTrue(hero_cta.evaluate("node => node === document.activeElement"))
            self.assertIsNone(hero_cta.get_attribute("tabindex"))
        finally:
            context.close()

    def test_initial_viewport_reveal_targets_are_never_hidden(self) -> None:
        context = self.browser.new_context()
        page = context.new_page()
        try:
            page.goto(
                f"{self.base_url}/hizmetler/",
                wait_until="domcontentloaded",
            )
            page.wait_for_selector('html[data-v-motion="ready"]')
            in_view_reveals_are_visible = page.evaluate(
                """
                () => Array.from(document.querySelectorAll('.v-motion-reveal'))
                  .filter((node) => {
                    const rect = node.getBoundingClientRect();
                    return rect.top < window.innerHeight && rect.bottom > 0;
                  })
                  .every((node) => node.classList.contains('is-visible') && getComputedStyle(node).opacity === '1')
                """
            )

            self.assertTrue(in_view_reveals_are_visible)
        finally:
            context.close()

    def test_no_javascript_keeps_primary_content_visible(self) -> None:
        context = self.browser.new_context(java_script_enabled=False)
        page = context.new_page()
        try:
            response = page.goto(
                f"{self.base_url}/hizmetler/",
                wait_until="domcontentloaded",
            )

            self.assertIsNotNone(response)
            self.assertEqual(200, response.status)
            self.assertTrue(page.locator("h1").is_visible())
            self.assertEqual(0, page.locator(".v-scroll-track").count())
            self.assertFalse(
                page.locator("html").evaluate(
                    "node => node.classList.contains('v-motion-enabled')"
                )
            )
        finally:
            context.close()

    def test_mobile_motion_does_not_create_horizontal_overflow(self) -> None:
        context = self.browser.new_context(
            viewport={"width": 390, "height": 844},
            has_touch=True,
            is_mobile=True,
        )
        page = context.new_page()
        try:
            page.goto(
                f"{self.base_url}/hizmetler/",
                wait_until="domcontentloaded",
            )
            page.wait_for_selector("html.v-motion-enabled")
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
            )

            self.assertLessEqual(overflow, 1)
            self.assertEqual(0, page.locator(".v-motion-card-glow").count())
        finally:
            context.close()


if __name__ == "__main__":
    unittest.main()
