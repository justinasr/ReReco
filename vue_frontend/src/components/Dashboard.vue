<template>
  <div>
    <h1>System Dashboard</h1>
    <div style="margin: 8px">
      <h3>Submission threads</h3>
      <ul>
        <li v-for="(info, worker) in submission_workers" :key="worker">Thread "{{worker}}" is {{info.job_name ? 'working on ' + info.job_name + ' for ' + info.job_time + 's' : 'not busy'}}</li>
      </ul>
      <h3>Locked objects</h3>
      <ul>
        <li v-for="(info, lock) in locks" :key="lock">{{lock}}:<ul><li>Info: {{info.i}}</li><li>Lock: {{info.l}}</li></ul></li>
      </ul>
    </div>
  </div>
</template>

<script>

import axios from 'axios'

export default {
  components: {
  },
  data () {
    return {
      submission_workers: [],
      locks: []
    }
  },
  created () {
    this.fetchWorkerInfo();
    this.fetchLocksInfo();
    setInterval(this.fetchWorkerInfo, 10000);
    setInterval(this.fetchLocksInfo, 10000);
  },
  methods: {
    fetchWorkerInfo () {
      let component = this;
      axios.get('api/system/workers').then(response => {
        component.submission_workers = response.data.response;

      });
    },
    fetchLocksInfo () {
      let component = this;
      axios.get('api/system/locks').then(response => {
        component.locks = response.data.response;

      });
    }
  }
}
</script>

<style scoped>

h1 {
  margin: 8px;
}

</style>