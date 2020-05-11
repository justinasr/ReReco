<template>
  <div>
    <h1>Chained Campaigns</h1>
    <ColumnSelector :columns="columns"
                    v-on:updateColumns="updateTableColumns"/>
    <v-data-table :headers="headers"
                  :items="dataItems"
                  :items-per-page="itemsPerPage"
                  :mobile-breakpoint=NaN
                  disable-sort
                  hide-default-footer
                  class="elevation-1">
      <template v-slot:item._actions="{ item }">
        &gt;&gt;Actions go here&lt;&lt;
      </template>
      <template v-slot:item.history="{ item }">
        <pre>{{JSON.stringify(item.history, null, 2)}}</pre>
      </template>
      <template v-slot:item.campaigns="{ item }">
        <pre>{{JSON.stringify(item.campaigns, null, 2)}}</pre>
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
  components: {
    ColumnSelector,
    Paginator
  },
  data () {
    return {
      databaseName: undefined,
      columns: [
        {'dbName': 'prepid', 'displayName': 'PrepID', 'visible': 1},
        {'dbName': '_actions', 'displayName': 'Actions', 'visible': 1},
        {'dbName': 'campaigns', 'displayName': 'Chained Campaign Structure', 'visible': 1}
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
      axios.get('api/search?db_name=chained_campaigns' + queryParams).then(response => {
        component.dataItems = response.data.response.results.map(function (x) { x._actions = undefined; return x});
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

</style>