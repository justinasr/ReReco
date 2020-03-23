<template>
  <div class="subcampaigns">
    <h1>Home</h1>
    <div style="margin: 8px">
      <h3>ReReco objects:</h3>
      <ul>
        <li><a :href="'subcampaigns'">Subcampaigns</a></li>
        <li><a :href="'subcampaign_tickets'">Subcampaign tickets</a></li>
        <li><a :href="'requests'">Requests</a>
          <ul v-if="objectsInfo">
            <li v-for="by_status_entry in objectsInfo.by_status" :key="by_status_entry._id">
              <a :href="'requests?status=' + by_status_entry._id">{{by_status_entry._id}}</a> - {{by_status_entry.count}} requests
              <ul v-if="by_status_entry._id == 'submitted'">
                <li v-for="ps_entry in objectsInfo.by_processing_string" :key="ps_entry._id">
                  <a :href="'requests?status=submitted&processing_string=' + ps_entry._id">{{ps_entry._id}}</a> - {{ps_entry.count}} requests
                </li>
              </ul>
            </li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>

import axios from 'axios'

export default {
  name: 'home',
  components: {
    // HelloWorld
  },
  data () {
    return {
      objectsInfo: undefined
    }
  },
  created () {
    this.fetchObjectsInfo();
  },
  methods: {
    fetchObjectsInfo () {
      let component = this;
      axios.get('api/system/objects_info').then(response => {
        component.objectsInfo = response.data.response;

      });
    },
  }
}
</script>

<style scoped>

h1 {
  margin: 8px;
}

</style>
