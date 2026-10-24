"""Tests for scripts/render.py and the templates. Standard library only:

    python3 -m unittest discover -s plugins/knowledge-generator/tests
"""
import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import render as r  # noqa: E402

TEMPLATES = ROOT / "templates"
FIXTURES = ROOT / "tests" / "fixtures"
PROJECT_TPL = "local-tools/skills/{p}-knowledge-add-project/templates/{n}.md"
LIST_MARKERS = "local-tools/skills/{p}-knowledge-list-markers/SKILL.md"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def render_all(name):
    return dict(r.render_tree(TEMPLATES, load(name)))


class Engine(unittest.TestCase):
    def test_variable(self):
        self.assertEqual(r.render("a {{ x.y }} b", {"x": {"y": 3}}), "a 3 b")

    def test_unknown_name_is_an_error(self):
        with self.assertRaises(r.TemplateError):
            r.render("{{ nope }}", {})

    def test_non_scalar_is_an_error(self):
        with self.assertRaises(r.TemplateError):
            r.render("{{ x }}", {"x": [1]})

    def test_if_else(self):
        t = "{{#if a}}yes{{else}}no{{/if}}"
        self.assertEqual(r.render(t, {"a": True}), "yes")
        self.assertEqual(r.render(t, {"a": False}), "no")
        self.assertEqual(r.render(t, {"a": "none"}), "no")

    def test_unless(self):
        self.assertEqual(r.render("{{#unless a}}x{{/unless}}", {"a": ""}), "x")

    def test_each(self):
        ctx = {"l": [{"n": "a"}, {"n": "b"}]}
        self.assertEqual(r.render("{{#each l}}[{{ this.n }}]{{/each}}", ctx), "[a][b]")

    def test_each_over_strings_and_nesting(self):
        ctx = {"outer": [{"n": "a"}, {"n": "b"}], "inner": ["x", "y"]}
        t = "{{#each outer}}{{ this.n }}:{{#each inner}}{{ this }}{{/each}};{{/each}}"
        self.assertEqual(r.render(t, ctx), "a:xy;b:xy;")

    def test_standalone_block_lines_vanish(self):
        t = "one\n{{#if a}}\ntwo\n{{/if}}\nthree\n"
        self.assertEqual(r.render(t, {"a": True}), "one\ntwo\nthree\n")
        self.assertEqual(r.render(t, {"a": False}), "one\nthree\n")

    def test_inline_block_keeps_surroundings(self):
        self.assertEqual(r.render("a{{#if x}}b{{/if}}c", {"x": True}), "abc")
        self.assertEqual(r.render("a{{#if x}}b{{/if}}c", {"x": False}), "ac")

    def test_escape(self):
        self.assertEqual(r.render(r"\{{ keep }}", {}), "{{ keep }}")

    def test_unbalanced_blocks(self):
        for bad in ("{{#if a}}x", "x{{/if}}", "{{#if a}}{{/each}}", "{{else}}"):
            with self.assertRaises(r.TemplateError, msg=bad):
                r.render(bad, {"a": True})

    def test_single_braces_pass_through(self):
        t = '{ "query": {"match_phrase": {"project": "x"}}} and ${R}:path'
        self.assertEqual(r.render(t, {}), t)


class Config(unittest.TestCase):
    def test_fixtures_validate(self):
        for name in ("acme.config.json", "fakeco.config.json"):
            r.validate(load(name))

    def test_unknown_top_level_key(self):
        cfg = load("fakeco.config.json")
        cfg["extra"] = 1
        with self.assertRaises(r.ConfigError):
            r.validate(cfg)

    def test_own_team_must_exist(self):
        cfg = load("fakeco.config.json")
        cfg["scope"]["own_team"] = "NOPE"
        with self.assertRaises(r.ConfigError):
            r.validate(cfg)

    def test_capability_needs_kind(self):
        cfg = load("fakeco.config.json")
        del cfg["capabilities"]["logs"]["kind"]
        with self.assertRaises(r.ConfigError):
            r.validate(cfg)

    def test_audience_needs_deployed_flag(self):
        cfg = load("fakeco.config.json")
        del cfg["scope"]["audience"][0]["deployed"]
        with self.assertRaises(r.ConfigError):
            r.validate(cfg)

    def test_artifact_skeleton_needs_a_non_deployed_audience(self):
        cfg = load("fakeco.config.json")
        cfg["scope"]["audience"] = [dict(a, deployed=True) for a in cfg["scope"]["audience"]]
        with self.assertRaisesRegex(r.ConfigError, "deployed false"):
            r.validate(cfg)

    def test_a_settings_store_needs_a_lookup(self):
        cfg = load("acme.config.json")
        cfg["capabilities"]["global_settings"]["lookup"] = ""
        with self.assertRaisesRegex(r.ConfigError, "global_settings.lookup"):
            r.validate(cfg)

    def test_a_log_system_without_an_mcp_never_names_one(self):
        cfg = load("acme.config.json")
        cfg["capabilities"]["logs"]["access"] = "none"
        cfg["capabilities"]["metrics"]["access"] = "none"
        for name, text in dict(r.render_tree(TEMPLATES, cfg)).items():
            self.assertNotIn("`none` MCP", text, name)
            self.assertNotIn("via none", text, name)

    def test_unknown_skeleton(self):
        cfg = load("fakeco.config.json")
        cfg["stack"]["skeletons"] = ["service", "nope"]
        with self.assertRaises(r.ConfigError):
            r.validate(cfg)

    def test_reference_doc_lists_the_same_top_level_keys(self):
        text = (ROOT / "schema" / "config.reference.yaml").read_text(encoding="utf-8")
        self.assertEqual(set(re.findall(r"^([a-z_]+):", text, re.M)), r.TOP_KEYS)

    def test_empty_skeletons_derive_from_the_runtime(self):
        cfg = load("fakeco.config.json")
        cfg["stack"]["skeletons"] = []
        cfg["stack"]["runtime"]["presets"] = ["vm"]
        self.assertEqual(r.effective_skeletons(cfg), ["legacy-vm", "artifact"])
        cfg["stack"]["runtime"]["presets"] = ["kubernetes"]
        self.assertEqual(r.effective_skeletons(cfg), ["service", "artifact"])

    def test_derive(self):
        ctx = r.derive(load("acme.config.json"))
        self.assertEqual(ctx["names"]["list_markers"], "acme-knowledge-list-markers")
        self.assertTrue(ctx["has"]["logs"])
        self.assertTrue(ctx["has"]["shared_catalogs"])
        self.assertTrue(ctx["has"]["db_projects"])
        self.assertEqual(ctx["derived"]["knowledge_root"], "~/work/acme-docs/knowledge/skills/acme-knowledge")
        self.assertEqual(ctx["derived"]["envs_reversed"], ["prod", "stg", "dev"])
        ctx = r.derive(load("fakeco.config.json"))
        self.assertFalse(ctx["has"]["logs"])
        self.assertFalse(ctx["has"]["shared_catalogs"])
        self.assertFalse(ctx["has"]["db_projects"])
        self.assertEqual(ctx["derived"]["knowledge_root"], "~/code/northwind-knowledge/skills/nw-knowledge")

    def test_bootstrap_script_follows_paths_and_link_dir(self):
        script = r.derive(load("acme.config.json"))["derived"]["bootstrap_script"]
        self.assertIn("for item in knowledge/local-tools/skills/*", script)
        self.assertIn('"../../$item"', script)
        script = r.derive(load("fakeco.config.json"))["derived"]["bootstrap_script"]
        self.assertIn("for item in local-tools/skills/*", script)
        cfg = load("fakeco.config.json")
        cfg["kit"]["link_dir"] = ".agents/skills/links"
        self.assertIn('"../../../$item"', r.derive(cfg)["derived"]["bootstrap_script"])


class Templates(unittest.TestCase):
    def test_path_is_prefixed_and_suffix_dropped(self):
        self.assertIn(LIST_MARKERS.format(p="nw"), render_all("fakeco.config.json"))
        self.assertIn(LIST_MARKERS.format(p="acme"), render_all("acme.config.json"))

    def test_no_leftover_tags_or_placeholders(self):
        for name in ("acme.config.json", "fakeco.config.json"):
            for rel, text in render_all(name).items():
                self.assertNotIn("{{", text, rel)
                self.assertNotIn("__prefix__", rel)

    def test_the_anchor_scan_reads_whole_blocks_and_names_no_absent_capability(self):
        on = render_all("acme.config.json")[LIST_MARKERS.format(p="acme")]
        off = render_all("fakeco.config.json")[LIST_MARKERS.format(p="nw")]
        for text in (on, off):
            self.assertIn("/verified:/", text)
            self.assertNotIn("-A40", text)
        self.assertNotIn("global-setting", off)
        self.assertNotIn("liveness", off)

    def test_skeleton_selection_decides_which_templates_are_written(self):
        acme = render_all("acme.config.json")
        fake = render_all("fakeco.config.json")
        for n in ("service", "legacy-vm", "artifact"):
            self.assertIn(PROJECT_TPL.format(p="acme", n=n), acme)
        self.assertIn(PROJECT_TPL.format(p="nw", n="service"), fake)
        self.assertIn(PROJECT_TPL.format(p="nw", n="artifact"), fake)
        self.assertNotIn(PROJECT_TPL.format(p="nw", n="legacy-vm"), fake)

    def test_db_project_sections_follow_the_db_schema_capability(self):
        acme = render_all("acme.config.json")[PROJECT_TPL.format(p="acme", n="artifact")]
        fake = render_all("fakeco.config.json")[PROJECT_TPL.format(p="nw", n="artifact")]
        self.assertIn("## Databases", acme)
        self.assertNotIn("## Databases", fake)

    def test_catalog_field_becomes_a_bullet_per_catalog(self):
        acme = render_all("acme.config.json")[PROJECT_TPL.format(p="acme", n="service")]
        fake = render_all("fakeco.config.json")[PROJECT_TPL.format(p="nw", n="service")]
        self.assertIn("- **Redis**:", acme)
        self.assertNotIn("Redis", fake)

    def test_env_lists_follow_the_config(self):
        fake = render_all("fakeco.config.json")[PROJECT_TPL.format(p="nw", n="service")]
        self.assertIn("  - staging: <cluster / platform>", fake)
        self.assertIn("  - production: <cluster / platform>", fake)
        self.assertNotIn("uat", fake)
        acme = render_all("acme.config.json")[PROJECT_TPL.format(p="acme", n="service")]
        self.assertIn("Never a row for dr.", acme)

    def test_kubernetes_decides_the_environment_bullets(self):
        acme = render_all("acme.config.json")[PROJECT_TPL.format(p="acme", n="service")]
        fake = render_all("fakeco.config.json")[PROJECT_TPL.format(p="nw", n="service")]
        self.assertIn("- **Namespace**:", acme)
        self.assertNotIn("- **Namespace**:", fake)
        self.assertIn("- **Deployment**: <how and where it runs>", fake)

    def test_one_fixture_never_leaks_into_the_other(self):
        for rel, text in render_all("fakeco.config.json").items():
            for word in ("acme", "gitlab", "kafka", "elk"):
                self.assertNotIn(word, text.lower(), f"{word!r} leaked into {rel}")
        for rel, text in render_all("acme.config.json").items():
            for word in ("northwind", "nw-knowledge"):
                self.assertNotIn(word, text.lower(), f"{word!r} leaked into {rel}")


class SkillFrontmatter(unittest.TestCase):
    """The kit skills are maintainer commands: never selectable by the model."""

    def skills(self):
        for name in ("acme.config.json", "fakeco.config.json"):
            for rel, text in render_all(name).items():
                if rel.startswith("local-tools/") and rel.endswith("/SKILL.md"):
                    yield name, rel, text

    def test_every_kit_skill_is_command_only(self):
        seen = 0
        for _, rel, text in self.skills():
            fm = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
            self.assertIn("disable-model-invocation: true", fm, rel)
            self.assertNotIn("user-invocable: false", fm, rel)
            seen += 1
        self.assertGreaterEqual(seen, 8)

    def test_descriptions_disambiguate_instead_of_listing_triggers(self):
        for _, rel, text in self.skills():
            fm = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
            desc = re.search(r"^description:[ \t]*>-?\n((?:[ \t]+.*\n?)+)", fm + "\n", re.M).group(1)
            flat = " ".join(line.strip() for line in desc.splitlines())
            self.assertLessEqual(len(flat), 1024, rel)
            self.assertNotIn("Triggers:", flat, rel)
            self.assertNotIn("Use when", flat, rel)

    def test_templates_are_english_only(self):
        cjk = re.compile(r"[\u3400-\u9fff\uff00-\uffef]")
        for src in TEMPLATES.rglob("*"):
            if src.is_file():
                self.assertIsNone(cjk.search(src.read_text(encoding="utf-8")), f"non-English text in {src}")


class SeedFiles(unittest.TestCase):
    def test_seed_file_is_rendered_without_its_suffixes(self):
        files = render_all("acme.config.json")
        self.assertIn("local-tools/skills/acme-knowledge-local-rules.md", files)
        self.assertIn("# Acme local rules", files["local-tools/skills/acme-knowledge-local-rules.md"])

    def test_seed_paths(self):
        paths = r.seed_paths(TEMPLATES, load("acme.config.json"))
        self.assertEqual(paths, {
            "local-tools/skills/acme-knowledge-local-rules.md",
            "skills/acme-knowledge/references/project/index.md",
            "skills/acme-knowledge/references/domain/index.md",
            "skills/acme-knowledge/references/observability.md",
            "skills/acme-knowledge/references/platform-basics.md",
            "README.md",
        })

    def test_every_skill_that_reads_rules_points_at_the_local_file(self):
        files = render_all("acme.config.json")
        for rel in ("add-project/SKILL.md", "add-project/CHECKLIST.md", "add-domain/SKILL.md",
                    "add-domain/CHECKLIST.md", "verify/SKILL.md"):
            skill = rel.split("/")[0]
            path = f"local-tools/skills/acme-knowledge-{skill}/{rel.split('/')[1]}"
            self.assertIn("../acme-knowledge-local-rules.md", files[path], path)


class ReaderSkill(unittest.TestCase):
    """The reader skill is the opposite of the kit skills: the model must be able to pick it."""

    def frontmatter(self, name, prefix):
        text = render_all(name)[f"skills/{prefix}-knowledge/SKILL.md"]
        fm = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
        desc = re.search(r"^description:[ \t]*>-\n((?:[ \t]+.*\n?)+)", fm + "\n", re.M).group(1)
        return text, fm, " ".join(line.strip() for line in desc.splitlines())

    def test_it_is_model_selectable(self):
        for name, prefix in (("acme.config.json", "acme"), ("fakeco.config.json", "nw")):
            _, fm, _ = self.frontmatter(name, prefix)
            self.assertNotIn("disable-model-invocation", fm)
            self.assertNotIn("user-invocable", fm)

    def test_description_is_composed_from_the_config(self):
        _, _, desc = self.frontmatter("acme.config.json", "acme")
        self.assertTrue(desc.startswith("Acme project and business-flow knowledge across the Web Platform and Payments teams."))
        self.assertIn("Use when developing, debugging, reviewing, or planning any Acme project (storefront, checkout-api, billing-worker)", desc)
        self.assertIn("flow (checkout, refund, sign-in)", desc)
        self.assertIn("investigate it through ELK and Grafana data", desc)
        self.assertIn('"how does the checkout flow work"', desc)
        self.assertNotIn("Security", desc)

    def test_description_degrades_cleanly_without_examples_or_tools(self):
        _, _, desc = self.frontmatter("fakeco.config.json", "nw")
        self.assertEqual(
            desc,
            "Northwind project and business-flow knowledge across the Platform and Data teams. "
            "Use when developing, debugging, reviewing, or planning any Northwind project or flow; "
            "when the user names a project, team, or flow of Northwind; or asks about its architecture, "
            "dependencies, deployment, environments, or cross-project conventions.",
        )

    def test_description_stays_under_the_cap_or_the_config_is_rejected(self):
        for name, prefix in (("acme.config.json", "acme"), ("fakeco.config.json", "nw")):
            self.assertLessEqual(len(self.frontmatter(name, prefix)[2]), 1024)
        cfg = load("acme.config.json")
        cfg["reader"]["example_projects"] = [f"project-number-{i}" for i in range(200)]
        with self.assertRaises(r.ConfigError):
            r.derive(cfg)

    def test_the_two_load_bearing_how_to_use_items_are_always_there(self):
        for name, prefix in (("acme.config.json", "acme"), ("fakeco.config.json", "nw")):
            text, _, _ = self.frontmatter(name, prefix)
            self.assertIn("4. **Markers**", text)
            self.assertIn("5. **This doc gives you where to look, not the live answer", text)

    def test_blocks_table_follows_the_capabilities(self):
        acme = render_all("acme.config.json")["skills/acme-knowledge/SKILL.md"]
        fake = render_all("fakeco.config.json")["skills/nw-knowledge/SKILL.md"]
        self.assertIn("references/observability.md", acme)
        self.assertIn("Redis cluster catalog", acme)
        self.assertNotIn("observability.md", fake)
        self.assertNotIn("platform-basics.md", fake)

    def test_platform_basics_follow_the_chosen_categories(self):
        fake = render_all("fakeco.config.json")["skills/nw-knowledge/SKILL.md"]
        self.assertIn("- **Time**: <", fake)
        self.assertIn("- **Deployment**: <", fake)
        self.assertNotIn("- **CDN**", fake)


class RoutingSnippet(unittest.TestCase):
    def test_one_line_per_enabled_tool(self):
        acme = render_all("acme.config.json")["CLAUDE.snippet.md"]
        self.assertIn("the `elasticsearch` MCP", acme)
        self.assertIn("the `grafana` MCP", acme)
        self.assertIn("the settings CLI, by namespace", acme)
        fake = render_all("fakeco.config.json")["CLAUDE.snippet.md"]
        self.assertNotIn("MCP, loading its tools", fake)
        self.assertNotIn("the settings", fake)
        self.assertIn("`nw-knowledge`", fake)

    def test_local_repos_line_uses_the_repos_root(self):
        self.assertIn("`~/code/<repo>`", render_all("fakeco.config.json")["CLAUDE.snippet.md"])


class Readmes(unittest.TestCase):
    def test_root_readme_is_a_seed_the_user_owns(self):
        self.assertIn("README.md", r.seed_paths(TEMPLATES, load("acme.config.json")))
        self.assertNotIn("local-tools/README.md", r.seed_paths(TEMPLATES, load("acme.config.json")))

    def test_tier_table_lists_only_the_tools_that_are_configured(self):
        acme = render_all("acme.config.json")["README.md"]
        fake = render_all("fakeco.config.json")["README.md"]
        self.assertIn("the `elasticsearch` MCP (ELK), the `grafana` MCP (Grafana) and the settings CLI, by namespace", acme)
        self.assertNotIn("plus live tools", fake)
        self.assertIn("plus local repos under `~/code`", fake)

    def test_the_bootstrap_script_has_one_home_in_the_kit_readme(self):
        files = render_all("acme.config.json")
        script = r.derive(load("acme.config.json"))["derived"]["bootstrap_script"]
        self.assertNotIn(script, files["README.md"])
        self.assertIn('"Contributing a change" covers', files["README.md"])
        self.assertIn(script, files["local-tools/README.md"])
        update = files["local-tools/skills/acme-knowledge-update-skills/SKILL.md"]
        self.assertNotIn(script, update)
        self.assertIn('"Activate" in `knowledge/local-tools/README.md`', update)

    def test_kit_readme_names_every_kit_skill(self):
        text = render_all("acme.config.json")["local-tools/README.md"]
        for skill in ("add-project", "add-domain", "sync-local", "verify", "list-markers", "update-skills"):
            self.assertIn(f"acme-knowledge-{skill}/", text)
        self.assertIn("acme-knowledge-local-rules.md", text)

    def test_readme_blocks_follow_the_capabilities(self):
        acme = render_all("acme.config.json")["README.md"]
        fake = render_all("fakeco.config.json")["README.md"]
        self.assertIn("| `observability.md` |", acme)
        self.assertIn("| `platform-basics.md` |", acme)
        self.assertNotIn("observability.md", fake)
        self.assertNotIn("platform-basics.md", fake)

    def test_contributing_note_appears_only_when_set(self):
        cfg = load("fakeco.config.json")
        self.assertNotIn("Questions go to", dict(r.render_tree(TEMPLATES, cfg))["README.md"])
        cfg["kit"]["contributing_note"] = "Questions go to the docs channel."
        self.assertIn("Questions go to the docs channel.", dict(r.render_tree(TEMPLATES, cfg))["README.md"])


class SharedReferences(unittest.TestCase):
    OBS = "skills/{p}-knowledge/references/observability.md"
    PB = "skills/{p}-knowledge/references/platform-basics.md"

    def test_both_files_exist_only_when_their_capability_does(self):
        acme = render_all("acme.config.json")
        fake = render_all("fakeco.config.json")
        self.assertIn(self.OBS.format(p="acme"), acme)
        self.assertIn(self.PB.format(p="acme"), acme)
        self.assertNotIn(self.OBS.format(p="nw"), fake)
        self.assertNotIn(self.PB.format(p="nw"), fake)

    def test_every_reference_the_reader_skill_names_is_generated(self):
        for name, prefix in (("acme.config.json", "acme"), ("fakeco.config.json", "nw")):
            files = render_all(name)
            reader = files[f"skills/{prefix}-knowledge/SKILL.md"]
            for ref in ("observability.md", "platform-basics.md"):
                named = f"references/{ref}" in reader
                exists = f"skills/{prefix}-knowledge/references/{ref}" in files
                self.assertEqual(named, exists, f"{ref} named={named} exists={exists} for {prefix}")

    def test_observability_follows_the_logs_and_metrics_switches(self):
        text = render_all("acme.config.json")[self.OBS.format(p="acme")]
        self.assertIn("## Logging (ELK)", text)
        self.assertIn("| `app-logs` | server log | lucene |", text)
        self.assertIn("## Monitoring (Grafana)", text)
        self.assertIn("## Database schema", text)
        self.assertIn("one schema repo per database family", text)
        cfg = load("acme.config.json")
        cfg["capabilities"]["logs"] = {"kind": "none", "access": "none", "streams": []}
        cfg["capabilities"]["db_schema"] = {"kind": "none", "repos_hint": ""}
        only_metrics = dict(r.render_tree(TEMPLATES, cfg))[self.OBS.format(p="acme")]
        self.assertNotIn("## Logging", only_metrics)
        self.assertNotIn("## Database schema", only_metrics)
        self.assertIn("## Monitoring (Grafana)", only_metrics)

    def test_field_cross_reference_has_one_column_per_stream(self):
        cfg = load("acme.config.json")
        cfg["capabilities"]["logs"]["streams"] = [
            {"name": "server", "scope": "server log", "syntax": "lucene"},
            {"name": "client", "scope": "browser log", "syntax": "kql"},
        ]
        text = dict(r.render_tree(TEMPLATES, cfg))[self.OBS.format(p="acme")]
        self.assertIn("| Concept | `server` | `client` | ", text)
        self.assertIn("|---|---|---|", text)
        self.assertIn("| service identity | <field> | <field> |", text)

    def test_catalog_sections_and_anchors_follow_the_config(self):
        text = render_all("acme.config.json")[self.PB.format(p="acme")]
        self.assertIn("## Redis cluster catalog", text)
        self.assertIn("`- Redis:` line", text)
        self.assertIn("snapshot tables", text)
        cfg = load("acme.config.json")
        cfg["capabilities"]["shared_catalogs"].append(
            {"name": "queue", "source_field": "Queue", "heading": "Queue catalog"})
        text = dict(r.render_tree(TEMPLATES, cfg))[self.PB.format(p="acme")]
        self.assertIn("## Queue catalog", text)
        self.assertIn("- Queue catalog | source:", text)


FIXTURE_NAMES = sorted(p.name for p in FIXTURES.glob("*.config.json"))


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = r.main(argv)
    return code, out.getvalue(), err.getvalue()


def staged(tmp, name="acme.config.json"):
    """A copy of a fixture whose repository lives inside tmp, so a render stays out of the real tree."""
    cfg = load(name)
    cfg["paths"]["repo"] = str(Path(tmp) / "repo")
    path = Path(tmp) / "knowledge.config.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path, Path(tmp) / "repo" / cfg["paths"]["out"]


def plan_counts(text):
    m = re.match(r"plan: (\d+) new, (\d+) changed, (\d+) unchanged, (\d+) kept", text)
    return tuple(int(x) for x in m.groups()) if m else None


class Cli(unittest.TestCase):
    def test_by_default_nothing_is_written_and_a_good_config_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp)
            code, text, err = run(["--config", str(path)])
            self.assertEqual((code, err), (0, ""))
            new, changed, unchanged, kept = plan_counts(text)
            self.assertGreater(new, 15)
            self.assertEqual((changed, unchanged, kept), (0, 0, 0))
            self.assertFalse(out.exists())

    def test_a_bad_config_fails_with_a_message_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp)
            cfg = json.loads(path.read_text())
            cfg["scope"]["own_team"] = "NOPE"
            path.write_text(json.dumps(cfg))
            for argv in (["--config", str(path)], ["--config", str(path), "--write"]):
                code, text, err = run(argv)
                self.assertEqual((code, text), (1, ""))
                self.assertIn("own_team", err)
            self.assertFalse(out.exists())

    def test_a_missing_nested_key_is_reported_by_name_not_as_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp)
            cfg = json.loads(path.read_text())
            del cfg["capabilities"]["logs"]["access"]
            path.write_text(json.dumps(cfg))
            code, text, err = run(["--config", str(path), "--write"])
            self.assertEqual((code, text), (1, ""))
            self.assertIn("'access'", err)
            self.assertFalse(out.exists())

    def test_a_reader_description_over_the_cap_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = staged(tmp)
            cfg = json.loads(path.read_text())
            cfg["reader"]["example_flows"] = [f"flow-number-{i}" for i in range(200)]
            path.write_text(json.dumps(cfg))
            code, _, err = run(["--config", str(path)])
            self.assertEqual(code, 1)
            self.assertIn("1024", err)

    def test_write_renders_into_the_directory_the_config_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp)
            code, text, _ = run(["--config", str(path), "--write"])
            self.assertEqual(code, 0)
            self.assertTrue((out / "skills/acme-knowledge/SKILL.md").exists())
            self.assertRegex(text, r"done: wrote \d+, kept 0")

    def test_the_removed_switches_are_gone(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = staged(tmp)
            for flag in (["--validate"], ["--plan"], ["--out", tmp], ["--templates", tmp]):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    r.main(["--config", str(path)] + flag)

    def test_the_plan_reports_each_files_fate_and_shows_the_diff_of_a_changed_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp)
            run(["--config", str(path), "--write"])
            (out / "skills/acme-knowledge/SKILL.md").write_text("edited by hand\n", encoding="utf-8")
            (out / "README.md").write_text("my readme\n", encoding="utf-8")
            code, text, _ = run(["--config", str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(plan_counts(text)[1], 1)
            self.assertEqual(plan_counts(text)[3], len(r.seed_paths(TEMPLATES, load("acme.config.json"))))
            self.assertRegex(text, r"changed  skills/acme-knowledge/SKILL\.md  \(\+\d+ -1\)")
            self.assertIn("kept     README.md", text)
            self.assertIn("--- existing/skills/acme-knowledge/SKILL.md", text)
            self.assertIn("-edited by hand", text)
            self.assertEqual((out / "README.md").read_text(encoding="utf-8"), "my readme\n")

    def test_platform_basics_survive_regeneration_but_the_rest_of_the_reader_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp, "fakeco.config.json")
            run(["--config", str(path), "--write"])
            reader = out / "skills/nw-knowledge/SKILL.md"
            original = reader.read_text(encoding="utf-8")
            mine = original.replace("- **Time**: <", "- **Time**: UTC everywhere. <", 1)
            self.assertNotEqual(mine, original)
            reader.write_text(mine, encoding="utf-8")
            code, text, _ = run(["--config", str(path)])
            self.assertEqual((code, plan_counts(text)[1]), (0, 0))
            reader.write_text(mine.replace("## How to use", "## How I use", 1), encoding="utf-8")
            code, text, _ = run(["--config", str(path), "--write"])
            self.assertEqual(code, 0)
            fresh = reader.read_text(encoding="utf-8")
            self.assertIn("UTC everywhere.", fresh)
            self.assertIn("## How to use", fresh)

    def test_a_reader_with_its_keep_markers_removed_falls_back_to_the_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp, "fakeco.config.json")
            run(["--config", str(path), "--write"])
            reader = out / "skills/nw-knowledge/SKILL.md"
            original = reader.read_text(encoding="utf-8")
            reader.write_text(original.replace("<!-- keep -->\n", "").replace("<!-- /keep -->\n", ""), encoding="utf-8")
            code, text, _ = run(["--config", str(path), "--write"])
            self.assertEqual(code, 0)
            self.assertEqual(reader.read_text(encoding="utf-8"), original)

    def test_a_second_write_restores_generated_files_and_leaves_user_files_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = staged(tmp)
            run(["--config", str(path), "--write"])
            mine = out / "local-tools/skills/acme-knowledge-local-rules.md"
            generated = out / "local-tools/skills/acme-knowledge-list-markers/SKILL.md"
            mine.write_text("my rules\n", encoding="utf-8")
            generated.write_text("stale\n", encoding="utf-8")
            self.assertEqual(run(["--config", str(path), "--write"])[0], 0)
            self.assertEqual(mine.read_text(encoding="utf-8"), "my rules\n")
            self.assertNotEqual(generated.read_text(encoding="utf-8"), "stale\n")

    def test_the_config_is_never_modified_by_any_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = staged(tmp)
            before = path.read_text()
            run(["--config", str(path)])
            run(["--config", str(path), "--write"])
            self.assertEqual(path.read_text(), before)


class Presets(unittest.TestCase):
    def setUp(self):
        self.presets = json.loads((ROOT / "schema" / "presets.json").read_text(encoding="utf-8"))

    def test_it_covers_exactly_the_areas_the_renderer_knows(self):
        self.assertEqual(set(self.presets["stack"]), set(r.STACK_AREAS))
        self.assertEqual(set(self.presets["capabilities"]), set(r.CAPABILITIES))
        self.assertEqual(self.presets["platform_basics"], list(r.PLATFORM_BASICS))

    def test_every_fixture_uses_offered_presets_or_the_free_text_field(self):
        for name in FIXTURE_NAMES:
            cfg = load(name)
            for area in r.STACK_AREAS:
                for preset in cfg["stack"][area]["presets"]:
                    self.assertIn(preset, self.presets["stack"][area], f"{name}: {area}")
            for cap in r.CAPABILITIES:
                self.assertIn(cfg["capabilities"][cap]["kind"], self.presets["capabilities"][cap], f"{name}: {cap}")

    def test_every_named_tool_has_a_display_label(self):
        for cap, kinds in self.presets["capabilities"].items():
            for kind in kinds:
                if kind not in ("none", "central-store", "env-files", "repo-per-db", "migrations-in-repo"):
                    self.assertIn(kind, r.KIND_LABELS, f"{cap}: {kind}")


class EveryFixture(unittest.TestCase):
    """Invariants that hold for any valid config, the emptiest one included."""

    def test_each_fixture_validates_and_renders_without_leftovers(self):
        for name in FIXTURE_NAMES:
            r.validate(load(name))
            files = render_all(name)
            self.assertIn("README.md", files, name)
            for rel, text in files.items():
                self.assertNotIn("{{", text, f"{name}: {rel}")
                self.assertNotIn("__prefix__", rel)

    def test_every_kit_skill_is_command_only_and_the_reader_is_not(self):
        for name in FIXTURE_NAMES:
            prefix = load(name)["identity"]["prefix"]
            files = render_all(name)
            for rel, text in files.items():
                if rel.endswith("/SKILL.md"):
                    fm = re.match(r"---\n(.*?)\n---\n", text, re.S).group(1)
                    kit = rel.startswith("local-tools/")
                    self.assertEqual("disable-model-invocation: true" in fm, kit, f"{name}: {rel}")
            self.assertIn(f"skills/{prefix}-knowledge/SKILL.md", files)

    def test_the_emptiest_config_still_yields_a_usable_base(self):
        files = render_all("minimal.config.json")
        reader = files["skills/min-knowledge/SKILL.md"]
        self.assertIn("Minimal project and business-flow knowledge across the Core team.", reader)
        self.assertIn("4. **Markers**", reader)
        self.assertIn("5. **This doc gives you where to look", reader)
        self.assertNotIn("references/observability.md", reader)
        self.assertIn("none for this setup", files["local-tools/skills/min-knowledge-authoring-core.md"])
        self.assertIn(f"skills/min-knowledge/references/project/index.md", files)
        self.assertNotIn("skills/min-knowledge/references/observability.md", files)
        tpl = "local-tools/skills/min-knowledge-add-project/templates/{}.md"
        self.assertIn(tpl.format("artifact"), files)
        self.assertNotIn(tpl.format("service"), files)
        self.assertNotIn(tpl.format("legacy-vm"), files)


class RenderedKit(unittest.TestCase):
    """What a user ends up with after a render, run for real."""

    def rendered(self, name):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path, out = staged(tmp.name, name)
        self.assertEqual(run(["--config", str(path), "--write"])[0], 0)
        return Path(tmp.name) / "repo", out

    def test_every_rendered_skill_name_matches_its_directory(self):
        for name in FIXTURE_NAMES:
            _, out = self.rendered(name)
            for skill in out.rglob("SKILL.md"):
                fm = re.match(r"---\n(.*?)\n---\n", skill.read_text(), re.S).group(1)
                declared = re.search(r"^name:[ \t]*(\S+)", fm, re.M).group(1)
                self.assertEqual(declared, skill.parent.name, f"{name}: {skill}")
                self.assertRegex(fm, r"(?m)^description:")

    def test_the_bootstrap_script_links_every_kit_skill_and_the_links_resolve(self):
        import subprocess
        for name in FIXTURE_NAMES:
            repo, out = self.rendered(name)
            script = r.derive(load(name))["derived"]["bootstrap_script"]
            subprocess.run(["bash", "-c", script], cwd=repo, check=True)
            link_dir = repo / ".claude" / "skills"
            links = sorted(p.name for p in link_dir.iterdir())
            self.assertTrue(links, name)
            for link in link_dir.iterdir():
                self.assertTrue(link.is_symlink(), f"{name}: {link}")
                self.assertTrue(link.exists(), f"{name}: dangling {link}")
            prefix = load(name)["identity"]["prefix"]
            for skill in ("add-project", "add-domain", "sync-local", "verify", "list-markers", "update-skills"):
                self.assertIn(f"{prefix}-knowledge-{skill}", links, name)
                self.assertTrue((link_dir / f"{prefix}-knowledge-{skill}" / "SKILL.md").exists())

    def test_the_kit_skills_find_the_shared_rules_through_their_relative_pointer(self):
        _, out = self.rendered("acme.config.json")
        skills = out / "local-tools" / "skills"
        for skill in skills.glob("acme-knowledge-*/SKILL.md"):
            text = skill.read_text()
            for target in re.findall(r"\.\./(acme-knowledge-[a-z-]+\.md)", text):
                self.assertTrue((skills / target).exists(), f"{skill.parent.name} points at missing {target}")
            for target in re.findall(r"\.\./(acme-knowledge-[a-z-]+)/SKILL\.md", text):
                self.assertTrue((skills / target / "SKILL.md").exists(), f"{skill.parent.name} points at missing {target}")

    def test_a_second_render_is_a_no_op(self):
        for name in FIXTURE_NAMES:
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            path, out = staged(tmp.name, name)
            run(["--config", str(path), "--write"])
            _, text, _ = run(["--config", str(path)])
            new, changed, unchanged, kept = plan_counts(text)
            self.assertEqual((new, changed), (0, 0), f"{name}: {text.splitlines()[0]}")
            self.assertGreater(unchanged, 10, name)



if __name__ == "__main__":
    unittest.main()
