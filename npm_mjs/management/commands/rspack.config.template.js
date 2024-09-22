const rspack = require("@rspack/core") // eslint-disable-line no-undef

const settings = window.settings // Replaced by django-npm-mjs
const transpile = window.transpile // Replaced by django-npm-mjs


const predefinedVariables = {
    transpile_VERSION: transpile.VERSION
}

if (settings.DEBUG) {
    //baseRule.exclude = /node_modules/
    predefinedVariables.staticUrl = `(url => ${JSON.stringify(
        settings.STATIC_URL
    )} + url)`
} else if (
    settings.STATICFILES_STORAGE !==
    "npm_mjs.storage.ManifestStaticFilesStorage"
) {
    predefinedVariables.staticUrl = `(url => ${JSON.stringify(
        settings.STATIC_URL
    )} + url + "?v=" + ${transpile.VERSION})`
}

module.exports = {
    // eslint-disable-line no-undef
    mode: settings.DEBUG ? "development" : "production",
    // module: {
    //     rules: [] // [baseRule]
    // },
    output: {
        path: transpile.OUT_DIR,
        chunkFilename: transpile.VERSION + "-[id].js",
        publicPath: transpile.BASE_URL
    },
    plugins: [new rspack.DefinePlugin(predefinedVariables)],
    entry: transpile.ENTRIES
}
