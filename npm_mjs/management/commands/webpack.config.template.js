const webpack = require("webpack") // eslint-disable-line no-undef

const settings = window.settings // Replaced by django-npm-mjs
const transpile = window.transpile // Replaced by django-npm-mjs

const baseRule = {
    test: /\.(js|mjs)$/,
    use: {
        loader: "babel-loader",
        options: {
            presets: [
                "@babel/preset-env"
            ],
            plugins: [
                "@babel/plugin-syntax-dynamic-import"
            ]
        }
    }
}

if (settings.DEBUG) {
    baseRule.exclude = /node_modules/
}

module.exports = { // eslint-disable-line no-undef
    mode: settings.DEBUG ? 'development' : 'production',
    module: {
        rules: [baseRule]
    },
    output: {
        path: transpile.OUT_DIR,
        chunkFilename: transpile.VERSION + "-[id].js",
        publicPath: transpile.BASE_URL
    },
    plugins: [
        new webpack.DefinePlugin({
            "transpile_VERSION": transpile.VERSION
        })
    ],
    entry: transpile.ENTRIES
}
