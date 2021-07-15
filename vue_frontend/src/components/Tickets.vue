<template>
  <div style="height: calc(100vh - 118px); overflow: auto;">
    <div style="display: flex;">
      <div style="flex: 1 1 auto;">
        <div>
          <div style="width: calc(100vw - 32px); position: sticky; left: 16px;">
            <h1 class="page-title">Tickets</h1>
            <ColumnSelector :columns="columns"
                            v-on:updateColumns="updateTableColumns"/>
          </div>
        </div>
        <v-data-table :headers="headers"
                      :items="dataItems"
                      :items-per-page="itemsPerPage"
                      :loading="loading"
                      :options.sync="optionsSync"
                      :server-items-length="totalItems"
                      hide-default-footer
                      class="elevation-1"
                      dense>
          <template v-slot:item._actions="{ item }">
            <a :href="'tickets/edit?prepid=' + item.prepid" v-if="role('manager')" title="Edit ticket">Edit</a>&nbsp;
            <a style="text-decoration: underline;" @click="showDeleteDialog(item)" v-if="role('manager') && item.created_requests.length < 1" title="Delete ticket">Delete</a>&nbsp;
            <a v-if="role('manager')" :href="'tickets/edit?clone=' + item.prepid" title="Clone ticket">Clone</a>&nbsp;
            <a style="text-decoration: underline;" @click="showCreateRequestsDialog(item)" v-if="role('manager') && item.status == 'new'" title="Create requests from this ticket">Create requests</a>&nbsp;
            <a :href="'requests?ticket=' + item.prepid" v-if="item.created_requests && item.created_requests.length > 0" title="Show all requests created from this ticket">Show requests</a>&nbsp;
            <a :href="'api/tickets/twiki_snippet/' + item.prepid" v-if="item.status == 'done'" title="Show a snippet for TWiki">TWiki</a>&nbsp;
          </template>
          <template v-slot:item.prepid="{ item }">
            <a :href="'tickets?prepid=' + item.prepid" title="Show only this ticket">{{item.prepid}}</a>
          </template>
          <template v-slot:item.status="{ item }">
            <a :href="'tickets?status=' + item.status" :title="'Show all tickets with status ' + item.status">{{item.status}}</a>
          </template>
          <template v-slot:item.history="{ item }">
            <HistoryCell :data="item.history"/>
          </template>
          <template v-slot:item.input_datasets="{ item }">
            {{item.input_datasets.length}} input datasets:
            <ul style="line-height: 95%">
              <li v-for="dataset in item.input_datasets" :key="dataset">
                <small>
                  <a target="_blank" title="Open dataset in DAS" :href="makeDASLink(dataset)">
                    {{dataset}}
                  </a>
                </small>
              </li>
            </ul>
          </template>
          <template v-slot:item.steps="{ item }">
            <ul>
              <li v-for="(step, index) in item.steps" :key="index">
                Step {{index + 1}}:
                <ul>
                  <li>Subcampaign: <a :href="'subcampaigns?prepid=' + step.subcampaign" :title="'Open ' + step.subcampaign + ' subcampaign'">{{step.subcampaign}}</a></li>
                  <li>Processing string: <a :href="'requests?processing_string=' + step.processing_string" :title="'Show all requests with ' + step.processing_string + ' processing string'">{{step.processing_string}}</a></li>
                  <li>Time per event: {{step.time_per_event.join(' s, ')}} s</li>
                  <li>Size per event: {{step.size_per_event.join(' kB, ')}} kB</li>
                </ul>
              </li>
            </ul>
          </template>
          <template v-slot:item.created_requests="{ item }">
            <span v-if="item.created_requests && item.created_requests.length > 0"><a :href="'requests?ticket=' + item.prepid">{{item.created_requests.length}} requests:</a></span>
            <ul style="line-height: 95%">
              <li v-for="request in item.created_requests" :key="request">
                <small>
                  <a :href="'requests?prepid=' + request" :title="'Open ' + request + ' request'">
                    {{request}}
                  </a>
                </small>
              </li>
            </ul>
          </template>
          <template v-slot:item.notes="{ item }">
            <pre v-if="item.notes.length" v-html="sanitize(item.notes)" class="notes" v-linkified></pre>
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
          <span v-html="errorDialog.description"></span>
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
      <a :href="'tickets/edit'" v-if="role('manager')" title="Create new ticket">New ticket</a>
      <Paginator :totalRows="totalItems"
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
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  components: {
    ColumnSelector,
    Paginator,
    HistoryCell
  },
  mixins: [roleMixin, utilsMixin],
  data () {
    return {
      databaseName: undefined,
      columns: [
        {'dbName': 'prepid', 'displayName': 'PrepID', 'visible': 1, 'sortable': true},
        {'dbName': '_actions', 'displayName': 'Actions', 'visible': 1},
        {'dbName': 'status', 'displayName': 'Status', 'visible': 1, 'sortable': true},
        {'dbName': 'steps', 'displayName': 'Steps', 'visible': 1},
        {'dbName': 'input_datasets', 'displayName': 'Input Datasets', 'visible': 1},
        {'dbName': 'notes', 'displayName': 'Notes', 'visible': 1},
        {'dbName': 'created_requests', 'displayName': 'Created Requests', 'visible': 0},
        {'dbName': 'history', 'displayName': 'History', 'visible': 0, 'sortable': true},
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
      },
      optionsSync: {},
    }
  },
  computed: {
    visibleColumns: function () {
      return this.columns.filter(col => col.visible)
    }
  },
  watch: {
    optionsSync: {
      handler (newOptions, oldOptions) {
        if (!oldOptions.sortBy || !oldOptions.sortDesc || !newOptions.sortBy || !newOptions.sortDesc) {
          return;
        }
        let oldSortBy = undefined;
        if (oldOptions.sortBy.length) {
          oldSortBy = oldOptions.sortBy[0];
        }
        let oldSortAsc = undefined;
        if (oldOptions.sortDesc.length) {
          oldSortAsc = oldOptions.sortDesc[0];
        }
        let sortBy = undefined;
        if (newOptions.sortBy.length) {
          sortBy = newOptions.sortBy[0];
        }
        let sortAsc = undefined;
        if (newOptions.sortDesc.length) {
          sortAsc = newOptions.sortDesc[0];
        }
        if (oldSortBy === sortBy && oldSortAsc === sortAsc) {
          return;
        }
        let query = Object.assign({}, this.$route.query);
        if (sortBy !== undefined) {
          if (sortBy == 'history') {
            query['sort'] = 'created_on';
          } else {
            query['sort'] = sortBy;
          }
        } else {
          delete query['sort']
        }
        if (sortAsc !== undefined) {
          query['sort_asc'] = sortAsc ? 'true' : 'false';
        } else {
          delete query['sort_asc']
        }
        this.$router.replace({query: query}).catch(() => {});
        this.fetchObjects();
      },
      deep: true,
    },
  },
  created () {
    this.clearDialog();
    let query = Object.assign({}, this.$route.query);
    if ('sort' in query) {
      this.optionsSync.sortBy = [query['sort']];
    }
    if ('sort_asc' in query) {
      this.optionsSync.sortDesc = [query['sort_asc'] == 'true'];
    }
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
      axios.get('api/search?db_name=tickets' + queryParams).then(response => {
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
    showDeleteDialog: function(ticket) {
      let component = this;
      this.dialog.title = "Delete " + ticket.prepid + "?";
      this.dialog.description = "Are you sure you want to delete " + ticket.prepid + " ticket?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.delete('api/tickets/delete', {data: {'prepid': ticket.prepid}}).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error deleting ticket", component.getError(error));
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    showCreateRequestsDialog: function(ticket) {
      let component = this;
      this.dialog.title = "Create requests for " + ticket.prepid + "?";
      this.dialog.description = "Are you sure you want to generate requests for " + ticket.prepid + " ticket?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.post('api/tickets/create_requests', {'prepid': ticket.prepid}).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error creating requests", component.getError(error));
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
