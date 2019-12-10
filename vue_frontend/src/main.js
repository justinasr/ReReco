import Vue from 'vue'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify';

Vue.config.productionTip = false

var mixin = {
  created: function () {
    console.log('mixin hook called')
  }
}

new Vue({
  router,
  vuetify,
  mixin,
  render: h => h(App)
}).$mount('#app')