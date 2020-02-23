var webpack = require("webpack");

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

if (django.conf.settings.DEBUG) {
    baseRule.exclude = /node_modules/
}

module.exports = {
    mode: django.conf.settings.DEBUG ? 'development' : 'production',
    module: {
        rules: [baseRule]
    },
    output: {
        path: transpile.OUT_DIR,
        chunkFilename: transpile.VERSION + "-[id].js",
        publicPath: transpile.BASE_URL,
    },
    plugins: [
        new webpack.DefinePlugin({
            "transpile.VERSION": transpile.VERSION
        })
    ],
    entry: transpile.ENTRIES
}