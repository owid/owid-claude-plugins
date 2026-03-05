This repo is for developing Our World In Data related plugins for Claude Code.

Read @README.md for additional information

## Important: registering new plugins

Every new plugin directory added under `plugins/` **must** also be registered in `.claude-plugin/marketplace.json` to be discoverable and installable. Without this, the plugin will not appear in the marketplace, even if its `plugin.json` is correctly set up. Add an entry to the `plugins` array like:

```json
{
    "name": "your-plugin-name",
    "source": "./plugins/your-plugin-name"
}
```