<template>
  <div>
    <h1 class="page-title">Home</h1>
    <v-card raised class="page-card">
      <h3>Search:</h3>
      <wild-search></wild-search>
      <h3 class="mt-3">Quick links:</h3>
      <ul>
        <li><a :href="'tickets/edit'">Create new Ticket</a></li>
        <li><a :href="'requests?sort=created_on&sort_asc=false'">Newest Requests</a> - show requests with newest at the top</li>
        <li><a :href="'tickets?sort=created_on&sort_asc=false'">Newest Tickets</a> - show tickets with newest at the top</li>
      </ul>
      <h3 class="mt-3">Objects in ReReco database:</h3>
      <ul>
        <li><a :href="'subcampaigns'">Subcampaigns</a></li>
        <li><a :href="'tickets'">Tickets</a></li>
          <ul v-if="objectsInfo">
            <li v-for="by_status_entry in objectsInfo.tickets.by_status" :key="by_status_entry._id">
              <a :href="'tickets?status=' + by_status_entry._id">{{by_status_entry._id}}</a> - {{by_status_entry.count}} tickets
            </li>
          </ul>
        <li><a :href="'requests'">Requests</a>
          <ul v-if="objectsInfo">
            <li v-for="by_status_entry in objectsInfo.requests.by_status" :key="by_status_entry._id">
              <a :href="'requests?status=' + by_status_entry._id">{{by_status_entry._id}}</a> - {{by_status_entry.count}} requests
              <ul v-if="by_status_entry._id == 'submitted'">
                <li v-for="ps_entry in objectsInfo.requests.by_processing_string" :key="ps_entry._id">
                  <a :href="'requests?status=submitted&processing_string=' + ps_entry._id">{{ps_entry._id}}</a> - {{ps_entry.count}} requests
                </li>
              </ul>
            </li>
          </ul>
        </li>
      </ul>
    </v-card>
  </div>
</template>

<script>

import axios from 'axios'
import WildSearch from './WildSearch'

export default {
  name: 'home',
  components: {
    WildSearch
  },
  data () {
    return {
      objectsInfo: undefined,
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

