const webpack = require("webpack") // eslint-disable-line no-undef

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

if (settings.DEBUG) { // eslint-disable-line no-undef
    baseRule.exclude = /node_modules/
}

module.exports = { // eslint-disable-line no-undef
    mode: settings.DEBUG ? 'development' : 'production', // eslint-disable-line no-undef
    module: {
        rules: [baseRule]
    },
    output: {
        path: transpile.OUT_DIR, // eslint-disable-line no-undef
        chunkFilename: transpile.VERSION + "-[id].js", // eslint-disable-line no-undef
        publicPath: transpile.BASE_URL // eslint-disable-line no-undef
    },
    plugins: [
        new webpack.DefinePlugin({
            "transpile.VERSION": transpile.VERSION // eslint-disable-line no-undef
        })
    ],
    entry: transpile.ENTRIES // eslint-disable-line no-undef
}