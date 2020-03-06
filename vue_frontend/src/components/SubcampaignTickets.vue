<template>
  <div style="height: calc(100vh - 128px); overflow: auto;">
    <div style="display: flex;">
      <div style="flex: 1 1 auto;">
        <div>
          <div style="width: calc(100vw - 32px); position: sticky; left: 16px;">
            <h1>Subcampaign Tickets</h1>
            <ColumnSelector :columns="columns"
                            v-on:updateColumns="updateTableColumns"/>
          </div>
        </div>
        <v-data-table :headers="headers"
                      :items="dataItems"
                      :items-per-page="itemsPerPage"
                      :mobile-breakpoint=NaN
                      disable-sort
                      hide-default-footer
                      class="elevation-1">
          <template v-slot:item._actions="{ item }">
            <a :href="'subcampaign_tickets/edit?prepid=' + item.prepid" v-if="role('manager')">Edit</a>&nbsp;
            <a style="text-decoration: underline;" @click="showDeleteDialog(item)" v-if="role('manager')">Delete</a>&nbsp;
            <a style="text-decoration: underline;" @click="showCreateRequestsDialog(item)" v-if="role('manager') && item.status == 'new'">Create requests</a>&nbsp;
            <a :href="'api/subcampaign_tickets/twiki_snippet/' + item.prepid" v-if="item.status == 'done'">TWiki</a>&nbsp;
          </template>
          <template v-slot:item.history="{ item }">
            <HistoryCell :data="item.history"/>
          </template>
          <template v-slot:item.input_datasets="{ item }">
            {{item.input_datasets.length}} input datasets:
            <ul>
              <li v-for="dataset in item.input_datasets" :key="dataset"><small>{{dataset}}</small></li>
            </ul>
          </template>
          <template v-slot:item.created_requests="{ item }">
            <ul>
              <li v-for="prepid in item.created_requests" :key="prepid"><a :href="'requests?prepid=' + prepid">{{prepid}}</a></li>
            </ul>
          </template>
          <template v-slot:item.notes="{ item }">
            <pre v-if="item.notes.length" class="notes">{{item.notes}}</pre>
          </template>
          <template v-slot:item.time_per_event="{ item }">
            {{item.time_per_event}}s
          </template>
          <template v-slot:item.size_per_event="{ item }">
            {{item.size_per_event}} kB
          </template>
        </v-data-table>
      </div>
    </div>

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
          <v-btn small class="mr-1 mb-1" color="primary" @click="dialog.cancel">
            Cancel
          </v-btn>
          <v-btn small class="mr-1 mb-1" color="error" @click="dialog.ok">
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
          <v-btn small class="mr-1 mb-1" color="primary" @click="errorDialog.visible = false">
            Dismiss
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <footer>
      <a :href="'subcampaign_tickets/edit'" style="float: left; margin: 16px;" v-if="role('manager')">New ticket</a>
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
import HistoryCell from './HistoryCell'
import { roleMixin } from '../mixins/UserRoleMixin.js'

export default {
  components: {
    ColumnSelector,
    Paginator,
    HistoryCell
  },
  mixins: [roleMixin],
  data () {
    return {
      databaseName: undefined,
      columns: [
        {'dbName': 'prepid', 'displayName': 'PrepID', 'visible': 1},
        {'dbName': '_actions', 'displayName': 'Actions', 'visible': 1},
        {'dbName': 'status', 'displayName': 'Status', 'visible': 1},
        {'dbName': 'subcampaign', 'displayName': 'Subcampaign', 'visible': 1},
        {'dbName': 'input_datasets', 'displayName': 'Input Datasets', 'visible': 1},
        {'dbName': 'processing_string', 'displayName': 'Processing String', 'visible': 1},
        {'dbName': 'notes', 'displayName': 'Notes', 'visible': 1},
        {'dbName': 'created_requests', 'displayName': 'Created Requests', 'visible': 0},
        {'dbName': 'history', 'displayName': 'History', 'visible': 0},
        {'dbName': 'size_per_event', 'displayName': 'Size per Event', 'visible': 0},
        {'dbName': 'time_per_event', 'displayName': 'Time per Event', 'visible': 0},
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
      axios.get('api/search?db_name=subcampaign_tickets' + queryParams).then(response => {
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
    showDeleteDialog: function(subcampaign_ticket) {
      let component = this;
      this.dialog.title = "Delete " + subcampaign_ticket.prepid + "?";
      this.dialog.description = "Are you sure you want to delete " + subcampaign_ticket.prepid + " subcampaign ticket?";
      this.dialog.ok = function() {
        axios.delete('api/subcampaign_tickets/delete', {data: {'prepid': subcampaign_ticket.prepid, '_rev': subcampaign_ticket._rev}}).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          console.log(error.response.data);
          component.clearDialog();
          component.showError("Error deleting subcampaign ticket", error.response.data.message);
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    showCreateRequestsDialog: function(subcampaign_ticket) {
      let component = this;
      this.dialog.title = "Create requests for " + subcampaign_ticket.prepid + "?";
      this.dialog.description = "Are you sure you want to generate requests for " + subcampaign_ticket.prepid + " subcampaign ticket?";
      this.dialog.ok = function() {
        axios.post('api/subcampaign_tickets/create_requests', {'prepid': subcampaign_ticket.prepid}).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          console.log(error.response.data);
          component.clearDialog();
          component.showError("Error creating requests", error.response.data.message);
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

h1 {
  margin: 8px;
}

input[type="text"]:disabled {
  background: #dddddd;
}

</style>