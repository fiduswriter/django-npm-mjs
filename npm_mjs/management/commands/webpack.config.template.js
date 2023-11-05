const webpack = require("webpack") // eslint-disable-line no-undef

const settings = window.settings // Replaced by django-npm-mjs
const transpile = window.transpile // Replaced by django-npm-mjs

const baseRule = {
    test: /\.(js|mjs)$/,
    use: {
        loader: "babel-loader",
        options: {
            presets: ["@babel/preset-env"],
            plugins: [
                "@babel/plugin-syntax-dynamic-import",
                "@babel/plugin-proposal-optional-chaining"
            ]
        }
    }
}

const predefinedVariables = {
    transpile_VERSION: transpile.VERSION
}

if (settings.DEBUG) {
    baseRule.exclude = /node_modules/
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
    module: {
        rules: [baseRule]
    },
    output: {
        path: transpile.OUT_DIR,
        chunkFilename: transpile.VERSION + "-[id].js",
        publicPath: transpile.BASE_URL
    },
    plugins: [new webpack.DefinePlugin(predefinedVariables)],
    entry: transpile.ENTRIES
}
