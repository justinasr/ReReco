module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  publicPath: process.env.NODE_ENV !== 'production'
    ? ''
    : '/rereco',
  devServer: {
    port: 8003,
    logLevel: 'debug'
  }
}
