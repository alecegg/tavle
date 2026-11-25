# Test inventory

One row per test file under `tests/` (`test_*.py` and `components/*.test.js`), task 2.1.

- `tests`: Python rows count nodes from `pytest --collect-only -q`; JS rows count `rg -c "^\s*(it|test)\("`.
- `class` (design D3):
  - `asset-browser`: imports `playwright`, lives in `widget_matrix`, or reads files under the static tree (`UI_STATIC`, `UI_ROOT`, `files("tavle")` with `"static"`, or a `tavle/static` path).
  - `js`: `tests/components/*.test.js`, judged by Stryker.
  - `python`: all other files.
- Modules: Python rows list the `tavle` modules named in direct `import` or `from ... import` lines (a multi-line `from tavle import (...)` contributes only `tavle`). `-` means no direct tavle import. JS rows list `@ui/static` modules; `registry.js` loads every `static/components/*.js` and `load-mithril.js` loads `vendor/mithril.js`.
- `tests/components/charts_diagrams.test.js` builds its cases with `it.each`, which the rg pattern misses; its 82 comes from `npx vitest run` on that file.

| path | class | tests | tavle modules it imports |
| --- | --- | ---: | --- |
| tests/components/backend.test.js | js | 5 | `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/blocks_text.test.js | js | 3 | `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/callout.test.js | js | 2 | `@ui/static/components/mount.js`, `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/charts_diagrams.test.js | js | 82 | `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/code_diff.test.js | js | 3 | `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/containers.test.js | js | 6 | `@ui/static/components/mount.js`, `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/export_all.test.js | js | 3 | `-` |
| tests/components/inputs.test.js | js | 3 | `@ui/static/components/mount.js` |
| tests/components/inputs_markup.test.js | js | 17 | `@ui/static/components/*.js`, `@ui/static/vendor/mithril.js` |
| tests/components/mount.test.js | js | 2 | `@ui/static/components/mount.js`, `@ui/static/vendor/mithril.js` |
| tests/page/test_action_menu_browser.py | python | 11 | `tavle`, `tavle.page.actions` |
| tests/page/test_action_menu_drift.py | asset-browser | 6 | `tavle.page.actions`, `tavle.page.template` |
| tests/page/test_action_menu_touch.py | python | 7 | `tavle` |
| tests/page/test_actions.py | python | 91 | `tavle`, `tavle.page.actions` |
| tests/page/test_answers.py | python | 58 | `tavle`, `tavle.comments`, `tavle.comments.answers`, `tavle.comments.store`, `tavle.comments.watch` |
| tests/page/test_blocks_charts_diagrams.py | python | 77 | `tavle`, `tavle.blocks_render.charts`, `tavle.blocks_render.diagrams`, `tavle.blocks_render.flow`, `tavle.blocks_render.screen_flow`, `tavle.blocks_render.screens`, `tavle.blocks_render.sequence`, `tavle.blocks_render.state`, `tavle.components`, `tavle.page.render` |
| tests/page/test_blocks_code_diff.py | python | 64 | `tavle`, `tavle.blocks.change_summary`, `tavle.blocks_render.annotated_code`, `tavle.blocks_render.code`, `tavle.blocks_render.diff`, `tavle.blocks_render.file_tree`, `tavle.components`, `tavle.graph`, `tavle.page.render` |
| tests/page/test_blocks_decision.py | python | 10 | `tavle`, `tavle.page` |
| tests/page/test_blocks_help_parity.py | python | 35 | `tavle` |
| tests/page/test_blocks_inputs.py | python | 86 | `tavle`, `tavle.blocks_render.inputs`, `tavle.blocks_render.inputs_ordered`, `tavle.page.render` |
| tests/page/test_blocks_interactive.py | python | 10 | `tavle`, `tavle.page.render`, `tavle.page.template` |
| tests/page/test_blocks_render.py | python | 17 | `tavle`, `tavle.page.render` |
| tests/page/test_blocks_schema.py | python | 54 | `tavle`, `tavle.blocks_render`, `tavle.blocks_render.registry`, `tavle.blocks.spec`, `tavle.graph`, `tavle.lines`, `tavle.page.page_check` |
| tests/page/test_blocks_split.py | asset-browser | 6 | `tavle`, `tavle.blocks`, `tavle.blocks_render`, `tavle.page.include_statement`, `tavle.page.template` |
| tests/page/test_blocks_text.py | asset-browser | 35 | `tavle`, `tavle.blocks.decision`, `tavle.blocks.option_matrix`, `tavle.blocks_render.decision`, `tavle.page.render` |
| tests/page/test_cases_load.py | python | 3 | `tavle` |
| tests/page/test_chrome_design.py | asset-browser | 15 | `-` |
| tests/page/test_cli.py | asset-browser | 1 | `tavle` |
| tests/page/test_cli_commands.py | python | 5 | `-` |
| tests/page/test_cli_serve.py | python | 1 | `-` |
| tests/page/test_components_browser.py | python | 4 | `tavle` |
| tests/page/test_components_contract.py | asset-browser | 736 | `tavle`, `tavle.blocks_render.registry`, `tavle.components`, `tavle.page.render` |
| tests/page/test_design_tokens.py | asset-browser | 14 | `tavle.page.template`, `tavle.serve.serve` |
| tests/page/test_ds_tokens.py | asset-browser | 13 | `-` |
| tests/page/test_export_standalone.py | python | 3 | `tavle`, `tavle.components`, `tavle.page.template` |
| tests/page/test_extract_assemble.py | asset-browser | 23 | `tavle`, `tavle.page`, `tavle.page.assemble`, `tavle.serve.assemble_served`, `tavle.serve.serve` |
| tests/page/test_extract_blocks_schema.py | python | 34 | `tavle`, `tavle.lines`, `tavle.page.fences`, `tavle.page.markdown_syntax`, `tavle.page.page_check`, `tavle.page.render` |
| tests/page/test_extract_custom_removed.py | python | 1 | `tavle.serve.assemble_served` |
| tests/page/test_extract_include.py | python | 55 | `tavle`, `tavle.blocks`, `tavle.comments.store`, `tavle.page`, `tavle.page.actions`, `tavle.page.include`, `tavle.page.select` |
| tests/page/test_extract_inputs.py | python | 80 | `tavle.blocks_render.decision`, `tavle.comments.answers`, `tavle.page.page_check` |
| tests/page/test_extract_recipes.py | python | 5 | `tavle`, `tavle.blocks_render.common`, `tavle.blocks_render.inputs`, `tavle.page.render` |
| tests/page/test_extract_theme_coverage.py | asset-browser | 5 | `tavle`, `tavle.theme.css`, `tavle.theme.derive_shape`, `tavle.theme.presets` |
| tests/page/test_final_visual_fixes.py | asset-browser | 6 | `-` |
| tests/page/test_include_comments.py | python | 34 | `tavle`, `tavle.comments.comments`, `tavle.comments.store`, `tavle.comments.watch`, `tavle.page.include` |
| tests/page/test_inputs_basic.py | python | 22 | `tavle` |
| tests/page/test_inputs_ordered.py | asset-browser | 26 | `tavle`, `tavle.shell` |
| tests/page/test_no_status_edge_border.py | asset-browser | 2 | `-` |
| tests/page/test_no_typed_icons.py | python | 1 | `-` |
| tests/page/test_package.py | python | 2 | `tavle` |
| tests/page/test_page_header.py | asset-browser | 29 | `tavle.page.fences`, `tavle.page.header`, `tavle.page.render`, `tavle.page.select` |
| tests/page/test_page_mount_shadow.py | python | 11 | `tavle` |
| tests/page/test_page_theme_layers.py | python | 2 | `tavle` |
| tests/page/test_pages_block_types.py | python | 59 | `tavle.page.actions`, `tavle.page.fences`, `tavle.page.render` |
| tests/page/test_pages_comments.py | python | 28 | `tavle`, `tavle.comments.watch`, `tavle.listings`, `tavle.serve.assemble_served` |
| tests/page/test_pages_decision.py | asset-browser | 16 | `tavle`, `tavle.page`, `tavle.page.render` |
| tests/page/test_pages_remote.py | python | 13 | `tavle.serve`, `tavle.serve.serve` |
| tests/page/test_pages_render.py | python | 55 | `tavle.page`, `tavle.page.render` |
| tests/page/test_pages_review.py | python | 19 | `tavle`, `tavle.page.render`, `tavle.serve` |
| tests/page/test_pages_server.py | python | 40 | `tavle`, `tavle.page.template`, `tavle.serve` |
| tests/page/test_pages_toc.py | asset-browser | 19 | `tavle`, `tavle.page.render`, `tavle.page.toc` |
| tests/page/test_pages_ui.py | python | 25 | `tavle`, `tavle.page`, `tavle.page.assemble`, `tavle.page.render`, `tavle.serve.assemble_served` |
| tests/page/test_plan_board.py | asset-browser | 2 | `tavle` |
| tests/page/test_plan_board_progress.py | asset-browser | 1 | `tavle` |
| tests/page/test_plan_board_progress_validation.py | python | 2 | `tavle.blocks.tables` |
| tests/page/test_plan_board_sections.py | asset-browser | 4 | `tavle`, `tavle.page.assemble`, `tavle.page.render` |
| tests/page/test_recap_browser.py | python | 1 | `tavle` |
| tests/page/test_recap_page.py | python | 11 | `tavle`, `tavle.page.render` |
| tests/page/test_render_fragment.py | python | 2 | `tavle.page.assemble` |
| tests/page/test_review_comments.py | python | 13 | `tavle` |
| tests/page/test_rich_annotated_code.py | asset-browser | 12 | `tavle`, `tavle.blocks_render.annotated_code` |
| tests/page/test_rich_callout.py | python | 3 | `tavle`, `tavle.page.render` |
| tests/page/test_rich_change.py | asset-browser | 14 | `tavle`, `tavle.blocks.change`, `tavle.blocks_render.backend`, `tavle.blocks_render.change`, `tavle.page.render` |
| tests/page/test_rich_change_summary.py | python | 7 | `tavle`, `tavle.blocks.change_summary`, `tavle.page.render` |
| tests/page/test_rich_chart.py | asset-browser | 41 | `tavle`, `tavle.blocks.charts`, `tavle.blocks_render.chart_draw`, `tavle.blocks_render.chart_model`, `tavle.blocks_render.charts`, `tavle.blocks_render.chart_scale` |
| tests/page/test_rich_chart_events.py | python | 21 | `tavle`, `tavle.blocks.chart_notes`, `tavle.blocks_render.chart_events`, `tavle.blocks_render.chart_model`, `tavle.blocks_render.charts` |
| tests/page/test_rich_checklist.py | asset-browser | 8 | `tavle`, `tavle.page.render` |
| tests/page/test_rich_code.py | python | 4 | `tavle`, `tavle.blocks_render.code` |
| tests/page/test_rich_containers.py | asset-browser | 35 | `tavle`, `tavle.components`, `tavle.serve.assemble_served` |
| tests/page/test_rich_diagram.py | python | 30 | `tavle`, `tavle.blocks.diagrams`, `tavle.blocks_render.diagram_layout`, `tavle.blocks_render.diagrams` |
| tests/page/test_rich_diff.py | asset-browser | 16 | `tavle`, `tavle.blocks.diff_rows` |
| tests/page/test_rich_er.py | python | 21 | `tavle`, `tavle.blocks.backend`, `tavle.blocks_render.backend`, `tavle.blocks_render.er`, `tavle.blocks_render.er_layout`, `tavle.page.render` |
| tests/page/test_rich_file_tree.py | python | 14 | `tavle`, `tavle.blocks_render.file_tree` |
| tests/page/test_rich_flow.py | python | 12 | `tavle`, `tavle.blocks_render.flow`, `tavle.page.render` |
| tests/page/test_rich_image.py | python | 37 | `tavle`, `tavle.blocks.image`, `tavle.blocks.image_header`, `tavle.blocks_render.image`, `tavle.serve.assemble_served` |
| tests/page/test_rich_matrix.py | python | 14 | `tavle`, `tavle.page.render` |
| tests/page/test_rich_risk.py | asset-browser | 6 | `tavle`, `tavle.page.render` |
| tests/page/test_rich_screen_flow.py | asset-browser | 76 | `tavle`, `tavle.blocks_render.screen_flow`, `tavle.blocks_render.screen_flow_layout`, `tavle.blocks.screen_flow`, `tavle.page.render` |
| tests/page/test_rich_sequence.py | asset-browser | 25 | `tavle`, `tavle.blocks_render.sequence`, `tavle.blocks_render.sequence_layout`, `tavle.page.render` |
| tests/page/test_rich_state.py | asset-browser | 27 | `tavle`, `tavle.blocks_render.diagram_layout`, `tavle.blocks_render.state`, `tavle.blocks_render.state_graph`, `tavle.page.render` |
| tests/page/test_rich_stats.py | asset-browser | 6 | `tavle`, `tavle.page.render` |
| tests/page/test_rich_table.py | asset-browser | 39 | `tavle`, `tavle.blocks.tables` |
| tests/page/test_rich_timeline.py | asset-browser | 5 | `tavle`, `tavle.page.render` |
| tests/page/test_rich_wireframe.py | python | 58 | `tavle`, `tavle.blocks_render`, `tavle.blocks_render.screens`, `tavle.blocks.screens`, `tavle.page`, `tavle.page.render` |
| tests/page/test_row_kind_rules.py | python | 62 | `tavle`, `tavle.comments.store`, `tavle.page.actions`, `tavle.page.render` |
| tests/page/test_runtime_injection.py | asset-browser | 46 | `tavle`, `tavle.page.render` |
| tests/page/test_server_parts.py | python | 7 | `tavle.serve`, `tavle.serve.server_parts` |
| tests/page/test_static_js_syntax.py | asset-browser | 29 | `-` |
| tests/page/test_table_phone_cards.py | asset-browser | 7 | `tavle` |
| tests/page/test_theme_browser.py | python | 17 | `tavle` |
| tests/page/test_theme_export.py | python | 1 | `tavle`, `tavle.page.template` |
| tests/page/test_theme_page.py | python | 3 | `tavle`, `tavle.page.theme_page` |
| tests/page/test_theme_show.py | python | 3 | `tavle` |
| tests/page/test_visual_craft_mobile.py | python | 6 | `tavle` |
| tests/page/test_wheel_standalone.py | python | 1 | `-` |
| tests/page/test_widget_choice_design.py | asset-browser | 6 | `-` |
| tests/page/test_widget_comment_design.py | asset-browser | 2 | `-` |
| tests/page/test_widget_form_design.py | asset-browser | 3 | `-` |
| tests/page/test_widget_ranking_design.py | asset-browser | 7 | `-` |
| tests/page/test_widget_slider_design.py | asset-browser | 3 | `-` |
| tests/page/widget_matrix/test_matrix.py | asset-browser | 3432 | `-` |
| tests/page/widget_matrix/test_selftest.py | asset-browser | 19 | `-` |
| tests/test_block_tables.py | asset-browser | 14 | `tavle.blocks`, `tavle.blocks_render.registry`, `tavle.components` |
| tests/test_contrast.py | python | 16 | `tavle.contrast` |
| tests/test_contrast_values.py | python | 9 | `tavle.contrast` |
| tests/test_input_classic_scripts.py | asset-browser | 1 | `tavle.shell` |
| tests/test_lines_parse.py | python | 61 | `tavle.lines`, `tavle.lines.grammar` |
| tests/test_lines_stream.py | python | 12 | `tavle.lines`, `tavle.lines.grammar` |
| tests/test_pages_graph.py | python | 1 | `tavle.shell` |
| tests/test_public_api.py | python | 52 | `tavle` |
| tests/test_shell_assets.py | python | 7 | `tavle.shell` |
| tests/test_suite_rules.py | python | 4 | `-` |
| tests/test_svg_kit.py | python | 3 | `tavle.blocks_render` |
| tests/test_theme_css.py | python | 2 | `tavle`, `tavle.theme.css` |
| tests/test_theme_derive_colour.py | python | 2 | `tavle.contrast`, `tavle.theme.derive_colour` |
| tests/test_theme_derive_shape.py | asset-browser | 1 | `tavle.theme.derive_shape` |
| tests/test_theme_layers.py | python | 7 | `tavle.theme.layers`, `tavle.theme.tokens` |
| tests/test_theme_presets_load.py | asset-browser | 3 | `tavle.theme.presets`, `tavle.theme.tokens` |
| tests/test_theme_presets_valid.py | python | 5 | `tavle.theme.presets`, `tavle.theme.tokens`, `tavle.theme.validate` |
| tests/test_theme_tokens.py | python | 9 | `tavle.theme.tokens` |
| tests/test_theme_validate.py | python | 3 | `tavle.theme.derive_colour`, `tavle.theme.presets`, `tavle.theme.tokens`, `tavle.theme.validate` |
| tests/test_tokens_shared.py | asset-browser | 116 | `-` |
| tests/test_vendor_mithril.py | asset-browser | 3 | `-` |
| tests/test_widget_decision_design.py | python | 2 | `-` |
