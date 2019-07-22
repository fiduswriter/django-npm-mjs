var webpack = require("webpack");
module.exports = {
 mode: "$MODE$",
 module: {
  rules: [
   {
    $RULES$,
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
  ]
 },
 output: {
  path: "$OUT_DIR$",
  chunkFilename: "$VERSION$-[id].js",
  publicPath: "$TRANSPILE_BASE_URL$",
 },
 plugins: [
  new webpack.DefinePlugin({
   "process.env.TRANSPILE_VERSION": process.env.TRANSPILE_VERSION
  })
 ],
 entry: {
  $ENTRIES$
 }
}
