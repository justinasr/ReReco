<template>
  <div>
    <h1>Flows</h1>
    <ColumnSelector :columns="columns"
                    v-on:updateColumns="updateTableColumns"/>
    <v-data-table :headers="headers"
                  :items="dataItems"
                  :items-per-page="itemsPerPage"
                  :mobile-breakpoint=NaN
                  disable-sort
                  hide-default-footer
                  class="elevation-1">
      <template v-slot:item.notes="{ item }">
        <div class="notes">{{item.notes}}</div>
      </template>
      <template v-slot:item.history="{ item }">
        <pre>{{JSON.stringify(item.history, null, 4)}}</pre>
      </template>
      <template v-slot:item.request_parameters="{ item }">
        <pre>{{JSON.stringify(item.request_parameters, null, 4)}}</pre>
      </template>
      <template v-slot:item.source_campaigns="{ item }">
        <ul>
          <li v-for="campaign in item.source_campaigns" :key="campaign">{{campaign}}</li>
        </ul>
      </template>
    </v-data-table>
    <footer>
      <Paginator style="float: right;"
                 :totalRows="totalItems"
                 v-on:update="onPaginatorUpdate"/>
    </footer>
  </div>
</template>

<script>

import axios from 'axios'
import ColumnSelector from './ColumnSelector'
import Paginator from './Paginator'

export default {
  name: 'flows',
  components: {
    ColumnSelector,
    Paginator
  },
  data () {
    return {
      databaseName: undefined,
      columns: [
        {'dbName': 'prepid', 'displayName': 'PrepID', 'visible': 1},
        {'dbName': 'source_campaigns', 'displayName': 'Source campaigns', 'visible': 1},
        {'dbName': 'target_campaign', 'displayName': 'Target campaign', 'visible': 1},
        {'dbName': 'request_parameters', 'displayName': 'Request parameters', 'visible': 0},
        {'dbName': 'notes', 'displayName': 'Notes', 'visible': 1},
        {'dbName': 'history', 'displayName': 'History', 'visible': 0}
      ],
      headers: [],
      dataItems: [],
      loading: false,
      itemsPerPage: 1,  // If initial value is 0, table does not appear after update 
      totalItems: 0,
    }
  },
  computed: {
    visibleColumns: function () {
      return this.columns.filter(col => col.visible)
    }
  },
  created () {
    this.databaseName = 'flows';
  },
  methods: {
    fetchObjects () {
      let component = this;
      this.loading = true;
      let query = this.$route.query;
      let queryParams = '';
      Object.keys(query).forEach(k => {
        if (k != 'shown') {
          queryParams += '&' + k + '=' + query[k];
        }
      });
      axios.get('api/search?db_name=flows' + queryParams).then(response => {
        console.log(response.data);
        component.dataItems = response.data.response.results;
        component.totalItems = response.data.response.total_rows;
        component.loading = false;
      });
    },
    updateTableColumns: function(columns, headers) {
      this.columns = columns;
      this.headers = headers;
    },
    onPaginatorUpdate: function(page, itemsPerPage) {
      this.itemsPerPage = itemsPerPage;
      this.fetchObjects();
    }
  }
}
</script>

<style scoped>

.notes {
  background: #eee;
  padding: 6px;
  margin: 6px;
  box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.07);
  max-width: 350px;
  min-height: 33px;
}

</style>