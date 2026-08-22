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
    resolve: {
        // Resolve extensionless imports to TypeScript sources as well, so
        // that JS modules can be converted to TS by renaming them.
        extensions: [".tsx", ".ts", ".jsx", ".js", ".mjs", ".json", ".wasm"],
        extensionAlias: {
            // Allow importing TS modules with a ".js" suffix (and without
            // any extension) - common when converting JS sources to TS.
            ".js": [".ts", ".tsx", ".jsx", ".js"]
        }
    },
    module: {
        rules: [
            {
                // TypeScript sources (e.g. in a Django app's assets/js
                // or assets/ts folder) are transpiled with the built-in
                // SWC loader.
                test: /\.tsx?$/,
                use: [
                    {
                        loader: "builtin:swc-loader",
                        options: {
                            jsc: {
                                parser: {
                                    syntax: "typescript",
                                    tsx: true
                                },
                                target: "es2020"
                            }
                        }
                    }
                ]
            }
        ]
    },
    output: {
        path: transpile.OUT_DIR,
        chunkFilename: transpile.VERSION + "-[id].js",
        publicPath: transpile.BASE_URL
    },
    plugins: [new rspack.DefinePlugin(predefinedVariables)],
    entry: transpile.ENTRIES
}
