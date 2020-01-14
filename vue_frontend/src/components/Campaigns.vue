<template>
  <div>
    <h1>Campaigns</h1>
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
        <a :href="'campaigns/edit?prepid=' + item.prepid">Edit</a>
        &nbsp;
        <a style="text-decoration: underline;" @click="showDeleteDialog(item)">Delete</a>
      </template>
      <template v-slot:item.history="{ item }">
        <pre>{{JSON.stringify(item.history, null, 2)}}</pre>
      </template>
      <template v-slot:item.sequences="{ item }">
        <pre>{{JSON.stringify(item.sequences, null, 2)}}</pre>
      </template>
      <template v-slot:item.memory="{ item }">
        {{item.memory}} MB
      </template>
      <template v-slot:item.energy="{ item }">
        {{item.energy}} TeV
      </template>
      <template v-slot:item.cmssw_version="{ item }">
        {{item.cmssw_version.replace('_', ' ').replace(/_/g, '.')}}
      </template>
    </v-data-table>

    <v-dialog v-model="dialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">
          {{dialog.title}}
        </v-card-title>
        <v-card-text>
          {{dialog.description}}
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="dialog.cancel">
            Cancel
          </v-btn>
          <v-btn @click="dialog.ok">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="errorDialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">
          {{errorDialog.title}}
        </v-card-title>
        <v-card-text>
          {{errorDialog.description}}
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="errorDialog.visible = false">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <footer>
      <a :href="'campaigns/edit'">Create new campaign</a>
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
        {'dbName': 'type', 'displayName': 'Type', 'visible': 1},
        {'dbName': 'memory', 'displayName': 'Memory', 'visible': 1},
        {'dbName': 'cmssw_version', 'displayName': 'CMSSW Version', 'visible': 1},
        {'dbName': 'notes', 'displayName': 'Notes', 'visible': 1},
        {'dbName': 'energy', 'displayName': 'Energy', 'visible': 0},
        {'dbName': 'step', 'displayName': 'Step', 'visible': 0},
        {'dbName': 'sequences', 'displayName': 'Sequences', 'visible': 0},
        {'dbName': 'history', 'displayName': 'History', 'visible': 0},
      ],
      headers: [],
      dataItems: [],
      loading: false,
      itemsPerPage: 1,  // If initial value is 0, table does not appear after update
      totalItems: 0,
      dialog: {
        visible: false,
        title: '',
        description: '',
        cancel: undefined,
        ok: undefined,
      },
      errorDialog: {
        visible: false,
        title: '',
        description: ''
      }
    }
  },
  computed: {
    visibleColumns: function () {
      return this.columns.filter(col => col.visible)
    }
  },
  created () {
    this.clearDialog();
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
      axios.get('api/search?db_name=campaigns' + queryParams).then(response => {
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
    },
    clearDialog: function() {
      this.dialog.visible = false;
      this.dialog.title = '';
      this.dialog.description = '';
      this.dialog.ok = function() {};
      this.dialog.cancel = function() {};
    },
    clearErrorDialog: function() {
      this.errorDialog.visible = false;
      this.errorDialog.title = '';
      this.errorDialog.description = '';
    },
    showError: function(title, description) {
      this.clearErrorDialog();
      this.errorDialog.title = title;
      this.errorDialog.description = description;
      this.errorDialog.visible = true;
    },
    showDeleteDialog: function(campaign) {
      let component = this;
      this.dialog.title = "Delete " + campaign.prepid + "?";
      this.dialog.description = "Are you sure you want to delete " + campaign.prepid + " campaign?";
      this.dialog.ok = function() {
        axios.delete('api/campaigns/delete', {data: {'prepid': campaign.prepid, '_rev': campaign._rev}}).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          console.log(error.response.data);
          component.clearDialog();
          component.showError("Error deleting campaign", error.response.data.message);
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    }
  }
}
</script>

<style scoped>

</style>