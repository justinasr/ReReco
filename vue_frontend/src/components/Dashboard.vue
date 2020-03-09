<template>
  <div>
    <h1>System Dashboard</h1>
    <div style="margin: 8px">
      <h3>Submission threads ({{Object.keys(submission_workers).length}})</h3>
      <ul>
        <li v-for="(info, worker) in submission_workers" :key="worker">Thread "{{worker}}" is {{info.job_name ? 'working on ' + info.job_name + ' for ' + info.job_time + 's' : 'not busy'}}</li>
      </ul>
      <h3>Submission queue ({{submission_queue.length}})</h3>
      <ul>
        <li v-for="name in submission_queue" :key="name">{{name}}</li>
      </ul>
      <h3>Settings ({{Object.keys(settings).length}})</h3>
      <ul>
        <li v-for="setting in settings" :key="setting._id">{{setting._id}}: <pre>{{JSON.stringify(setting.value, null, 2)}}</pre></li>
      </ul>
      <h3>Locked objects ({{Object.keys(locks).length}})</h3>
      <ul>
        <li v-for="(info, lock) in locks" :key="lock">{{lock}}:
          <small>
            <ul>
              <li>Info: {{info.i}}</li>
              <li>Lock: {{info.l}}</li>
            </ul>
        </small>
        </li>
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
      submission_queue: [],
      locks: [],
      settings: [],
    }
  },
  created () {
    this.fetchWorkerInfo();
    this.fetchLocksInfo();
    this.fetchQueueInfo();
    this.fetchSettings();
    setInterval(this.fetchWorkerInfo, 10000);
    setInterval(this.fetchQueueInfo, 10000);
    setInterval(this.fetchLocksInfo, 10000);
  },
  methods: {
    fetchWorkerInfo () {
      let component = this;
      axios.get('api/system/workers').then(response => {
        component.submission_workers = response.data.response;

      });
    },
    fetchQueueInfo () {
      let component = this;
      axios.get('api/system/queue').then(response => {
        component.submission_queue = response.data.response;

      });
    },
    fetchLocksInfo () {
      let component = this;
      axios.get('api/system/locks').then(response => {
        component.locks = response.data.response;

      });
    },
    fetchSettings () {
      let component = this;
      axios.get('api/settings/get').then(response => {
        component.settings = response.data.response;
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