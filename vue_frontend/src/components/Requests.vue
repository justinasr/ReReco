<template>
  <div style="height: calc(100vh - 118px); overflow: auto;">
    <div style="display: flex;">
      <div style="flex: 1 1 auto;">
        <div>
          <div style="width: calc(100vw - 32px); position: sticky; left: 16px;">
            <h1 class="page-title">Requests</h1>
            <ColumnSelector :columns="columns"
                            v-on:updateColumns="updateTableColumns"/>
          </div>
        </div>
        <v-data-table :headers="headers"
                      :items="dataItems"
                      :items-per-page="itemsPerPage"
                      :options.sync="optionsSync"
                      :loading="loading"
                      :server-items-length="totalItems"
                      show-select
                      hide-default-footer
                      item-key="prepid"
                      class="elevation-1"
                      v-model="selectedItems"
                      dense>
          <template v-slot:item._actions="{ item }">
            <div class="actions">
              <a v-if="role('manager')" :href="'requests/edit?prepid=' + item.prepid" title="Edit request">Edit</a>
              <a v-if="role('manager') && item.status == 'new'" @click="deleteRequest(item)" title="Delete request">Delete</a>
              <a v-if="role('manager')" :href="'requests/edit?clone=' + item.prepid" title="Clone request">Clone</a>
              <a :href="'api/requests/get_cmsdriver/' + item.prepid" title="Show cmsDriver.py command for this request">cmsDriver</a>
              <a :href="'api/requests/get_dict/' + item.prepid" title="Show JSON dictionary for ReqMgr2">Job dict</a>
              <a @click="previousStatus(item)" v-if="role('manager') && item.status != 'new'" title="Move to previous status">Previous</a>
              <a @click="nextStatus(item)" v-if="role('manager') && item.status != 'done'" title="Move to next status">Next</a>
              <a @click="updateWorkflows(item)" v-if="role('administrator') && item.status == 'submitted' && !isDev" title="Update request information from Stats2">Update from Stats2</a>
              <a @click="optionReset(item)" v-if="role('manager') && item.status == 'new'" :title="'Refetch values from ' + item.subcampaign + ' subcampaign'">Option reset</a>
              <a target="_blank" :href="'https://cms-pdmv.cern.ch/stats?prepid=' + item.prepid" v-if="item.status == 'submitted' || item.status == 'done' && !isDev" title="Show workflows of this request in Stats2">Stats2</a>
              <a :href="'tickets?created_requests=' + item.prepid" title="Show ticket that was used to create this request">Ticket</a>
            </div>
          </template>
          <template v-slot:item.history="{ item }">
            <HistoryCell :data="item.history"/>
          </template>
          <template v-slot:item.prepid="{ item }">
            <a :href="'requests?prepid=' + item.prepid" title="Show only this request">{{item.prepid}}</a>
          </template>
          <template v-slot:item.status="{ item }">
            <a :href="'requests?status=' + item.status" :title="'Show requests with status ' + item.status">{{item.status}}</a>
          </template>
          <template v-slot:item.processing_string="{ item }">
            <a :href="'requests?processing_string=' + item.processing_string" :title="'Show requests with ' + item.processing_string + ' processing string'">{{item.processing_string}}</a>
          </template>
          <template v-slot:item.subcampaign="{ item }">
            <a :href="'requests?subcampaign=' + item.subcampaign" :title="'Show all requests in ' + item.subcampaign">{{item.subcampaign}}</a>&nbsp;
            <a :href="'subcampaigns?prepid=' + item.subcampaign" :title="'Open ' + item.subcampaign + ' subcampaign'">Subcampaign</a>
          </template>
          <template v-slot:item.sequences="{ item }">
            <SequencesCell :data="item.sequences"/>
          </template>
          <template v-slot:item.memory="{ item }">
            {{item.memory}} MB
          </template>
          <template v-slot:item.energy="{ item }">
            {{item.energy}} TeV
          </template>
          <template v-slot:item.cmssw_release="{ item }">
            <a :href="'requests?cmssw_release=' + item.cmssw_release" :title="'Show all requests with ' + item.cmssw_release">{{item.cmssw_release}}</a>
          </template>
          <template v-slot:item.notes="{ item }">
            <pre v-if="item.notes.length" v-html="sanitize(item.notes)" class="notes" v-linkified></pre>
          </template>
          <template v-slot:item.time_per_event="{ item }">
            {{item.time_per_event.join(' s, ')}} s
          </template>
          <template v-slot:item.size_per_event="{ item }">
            {{item.size_per_event.join(' kB, ')}} kB
          </template>
          <template v-slot:item.completed_events="{ item }">
            {{item.niceCompletedEvents}} <small v-if="item.total_events > 0">({{(100.0 * item.completed_events / item.total_events).toFixed(2)}}%)</small>
          </template>
          <template v-slot:item.total_events="{ item }">
            {{item.niceTotalEvents}}
          </template>
          <template v-slot:item.runs="{ item }">
            <span v-if="item.runs.length">{{item.runs.length}} runs: <small>{{item.runs.join(', ')}}</small></span>
          </template>
          <template v-slot:item.input="{ item }">
            <ul v-if="item.input">
              <li v-if="item.input.dataset">
                Dataset: <a target="_blank" title="Open dataset in DAS" :href="makeDASLink(item.input.dataset)">{{item.input.dataset}}</a>
              </li>
              <li v-if="item.input.request">
                Request: <a :href="'requests?prepid=' + item.input.request" :title="'Open ' + item.input.request + ' request'">{{item.input.request}}</a>
              </li>
            </ul>
          </template>
          <template v-slot:item.workflows="{ item }">
            <ol>
              <li v-for="(workflow, index) in item.workflows" :key="workflow.name">
                <a v-if="!isDev" target="_blank" title="Open workflow in ReqMgr2" :href="'https://cmsweb.cern.ch/reqmgr2/fetch?rid=' + workflow.name">{{workflow.name}}</a>&nbsp;
                <a v-if="isDev" target="_blank" title="Open workflow in ReqMgr2" :href="'https://cmsweb-testbed.cern.ch/reqmgr2/fetch?rid=' + workflow.name">{{workflow.name}}</a>&nbsp;
                <template v-if="!isDev">
                  <small> open in:</small> <a target="_blank" title="Open workflow in Stats2" :href="'https://cms-pdmv.cern.ch/stats?workflow_name=' + workflow.name">Stats2</a>&nbsp;
                </template>
                <template v-if="workflow.status_history && workflow.status_history.length > 0">
                  <small> status:</small> {{workflow.status_history[workflow.status_history.length - 1].status}}
                </template>
                <ul v-if="index == item.workflows.length - 1" class="zebra-datasets">
                  <li v-for="dataset in workflow.output_datasets" :key="dataset.name">
                    <div>
                      <div class="gray-bar">
                        <div :style="'width: ' +  dataset.completed + '%;'" :class="'bar ' + dataset.type.toLowerCase() + '-bar'"></div>
                      </div>
                      <small>datatier:</small> {{dataset.datatier}},
                      <small>completed:</small> {{dataset.completed}}%,
                      <small>events:</small> {{dataset.niceEvents}},
                      <small>type:</small> <b :class="dataset.type.toLowerCase() + '-type'">{{dataset.type}}</b>
                      <br>
                      <a target="_blank" title="Open dataset in DAS" :href="makeDASLink(dataset.name)">{{dataset.name}}</a>
                    </div>
                  </li>
                </ul>
              </li>
            </ol>
          </template>
          <template v-slot:item.output_datasets="{ item }">
            <ul>
              <li v-for="dataset in item.output_datasets" :key="dataset"><a target="_blank" title="Open dataset in DAS" :href="makeDASLink(dataset)">{{dataset}}</a></li>
            </ul>
          </template>
          <template v-slot:item.lumisections="{ item }">
            <pre><small>{{stringifyLumis(item.lumisections)}}</small></pre>
          </template>
          <template v-slot:item._gpu="{ item }">
            <ul style="padding-left: 0; list-style: none;">
              <li v-for="(sequence, index) in item.sequences" :key="index">
                <template v-if="sequenceSteps(sequence)">
                  {{sequenceSteps(sequence)}}: {{sequence.gpu.requires}}
                  <ul v-if="sequence.gpu.requires != 'forbidden'">
                    <li v-if="sequence.gpu.gpu_memory">GPUMemory: {{sequence.gpu.gpu_memory}} MB</li>
                    <li v-if="sequence.gpu.cuda_capabilities.length">CUDACapabilities: {{sequence.gpu.cuda_capabilities.join(',')}}</li>
                    <li v-if="sequence.gpu.cuda_runtime">CUDARuntime: {{sequence.gpu.cuda_runtime}}</li>
                    <li v-if="sequence.gpu.gpu_name">GPUName: {{sequence.gpu.gpu_name}}</li>
                    <li v-if="sequence.gpu.cuda_driver_version">CUDADriverVersion: {{sequence.gpu.cuda_driver_version}}</li>
                    <li v-if="sequence.gpu.cuda_runtime_version">CUDARuntimeVersion: {{sequence.gpu.cuda_runtime_version}}</li>
                  </ul>
                </template>
              </li>
            </ul>
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
      <div class="actions" style="float: left; line-height: 52px">
        <a :href="'requests/edit'" v-if="role('manager') && !selectedItems.length" title="Create new request">New request</a>
        <span v-if="role('manager') && selectedItems.length">Selected items ({{selectedItems.length}}) actions:</span>
        <a v-if="role('manager') && selectedItems.length > 1" @click="editRequests(selectedItems)" title="Edit selected requests">Edit</a>
        <a v-if="role('manager') && selectedItems.length" @click="deleteManyRequests(selectedItems)" title="Delete selected requests">Delete</a>
        <a v-if="role('manager') && selectedItems.length" @click="previousMany(selectedItems)" title="Move selected requests to previous status">Previous</a>
        <a v-if="role('manager') && selectedItems.length" @click="nextStatusMany(selectedItems)" title="Move selected requets to next status">Next</a>
        <a v-if="role('manager') && selectedItems.length" @click="createTicket(selectedItems)" title="Create a ticket with selected requests as input">Create ticket</a>
        <a v-if="role('administrator') && selectedItems.length" @click="updateWorkflowsMany(selectedItems)" title="Update selected requests' information from Stats2">Update from Stats2</a>
        <a v-if="role('manager') && selectedItems.length" @click="optionResetMany(selectedItems)" title="Refetch selected requests' values from their subcampaigns">Option Reset</a>
        <a v-if="selectedItems.length" @click="openPmpMany(selectedItems)" title="Show selected requests in pMp">pMp</a>
      </div>
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
import SequencesCell from './SequencesCell'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  components: {
    ColumnSelector,
    Paginator,
    HistoryCell,
    SequencesCell
  },
  mixins: [roleMixin, utilsMixin],
  data () {
    return {
      databaseName: undefined,
      columns: [
        {'dbName': 'prepid', 'displayName': 'PrepID', 'visible': 1, 'sortable': true},
        {'dbName': '_actions', 'displayName': 'Actions', 'visible': 1},
        {'dbName': 'status', 'displayName': 'Status', 'visible': 1, 'sortable': true},
        {'dbName': 'input', 'displayName': 'Input', 'visible': 1},
        {'dbName': 'processing_string', 'displayName': 'Processing String', 'visible': 1, 'sortable': true},
        {'dbName': 'subcampaign', 'displayName': 'Subcampaign', 'visible': 1, 'sortable': true},
        {'dbName': 'notes', 'displayName': 'Notes', 'visible': 1},
        {'dbName': 'cmssw_release', 'displayName': 'CMSSW Release', 'visible': 0, 'sortable': true},
        {'dbName': 'completed_events', 'displayName': 'Completed Events', 'visible': 0, 'sortable': true},
        {'dbName': 'energy', 'displayName': 'Energy', 'visible': 0, 'sortable': true},
        {'dbName': '_gpu', 'displayName': 'GPU', 'visible': 0},
        {'dbName': 'history', 'displayName': 'History', 'visible': 0, 'sortable': true},
        {'dbName': 'memory', 'displayName': 'Memory', 'visible': 0, 'sortable': true},
        {'dbName': 'lumisections', 'displayName': 'Lumisections', 'visible': 0},
        {'dbName': 'output_datasets', 'displayName': 'Output datasets', 'visible': 0},
        {'dbName': 'priority', 'displayName': 'Priority', 'visible': 0, 'sortable': true},
        {'dbName': 'runs', 'displayName': 'Runs', 'visible': 0},
        {'dbName': 'sequences', 'displayName': 'Sequences', 'visible': 0},
        {'dbName': 'size_per_event', 'displayName': 'Size per Event', 'visible': 0, 'sortable': true},
        {'dbName': 'time_per_event', 'displayName': 'Time per Event', 'visible': 0, 'sortable': true},
        {'dbName': 'total_events', 'displayName': 'Total Events', 'visible': 0, 'sortable': true},
        {'dbName': 'workflows', 'displayName': 'Workflows', 'visible': 0},
      ],
      headers: [],
      dataItems: [],
      selectedItems: [],
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
      isDev: false,
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
    this.isDev = document.location.origin.includes('dev');
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
      axios.get('api/search?db_name=requests' + queryParams).then(response => {
        component.dataItems = response.data.response.results.map(function (x) { x._actions = undefined; return x});
        component.dataItems.forEach(item => {
          item.niceTotalEvents = item.total_events.toLocaleString('en-US');
          item.niceCompletedEvents = item.completed_events.toLocaleString('en-US');
          if (item.workflows && item.workflows.length) {
            const lastWorkflow = item.workflows[item.workflows.length - 1];
            if (lastWorkflow.output_datasets) {
              lastWorkflow.output_datasets.forEach(ds => {
                ds.datatier = ds.name.split('/').pop();
                ds.completed = (item.total_events > 0 ? (ds.events / item.total_events * 100) : 0).toFixed(2);
                ds.niceEvents = ds.events.toLocaleString('en-US');
              });
            }
          }
        })
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
    deleteRequest: function(request) {
      let component = this;
      this.dialog.title = "Delete " + request.prepid + "?";
      this.dialog.description = "Are you sure you want to delete " + request.prepid + " request?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.delete('api/requests/delete', {data: {'prepid': request.prepid}}).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error deleting request", component.getError(error));
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    deleteManyRequests: function(requests) {
      let component = this;
      this.dialog.title = "Delete " + requests.length + " requests?";
      this.dialog.description = "Are you sure you want to delete " + requests.length + " requests?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.delete('api/requests/delete', {data: requests.slice()}).then(() => {
          component.clearDialog();
          component.fetchObjects();
          component.selectedItems = [];
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error deleting requests", component.getError(error));
          component.selectedItems =  [];
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    nextStatus: function (request) {
      let component = this;
      this.loading = true;
      axios.post('api/requests/next_status', request).then(() => {
        component.fetchObjects();
      }).catch(error => {
        component.loading = false;
        component.clearDialog();
        component.showError("Error moving request to next status", component.getError(error));
      });
    },
    nextStatusMany: function (requests) {
      let component = this;
      this.loading = true;
      axios.post('api/requests/next_status', requests.slice()).then(() => {
        component.fetchObjects();
        component.selectedItems = [];
      }).catch(error => {
        component.loading = false;
        component.clearDialog();
        component.showError("Error moving requests to next status", component.getError(error));
        component.selectedItems = [];
      });
    },
    previousStatus: function(request) {
      let component = this;
      this.dialog.title = "Set " + request.prepid + " to previous status?";
      this.dialog.description = "Are you sure you want to set " + request.prepid + " request to previous status?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.post('api/requests/previous_status', request).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error moving request to previous status", component.getError(error));
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    previousMany: function(requests) {
      let component = this;
      this.dialog.title = "Set " + requests.length + " requests to previous status?";
      this.dialog.description = "Are you sure you want to set " + requests.length + " requests to previous status?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.post('api/requests/previous_status', requests.slice()).then(() => {
          component.clearDialog();
          component.fetchObjects();
          component.selectedItems = [];
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error moving requests to previous status", component.getError(error));
          component.selectedItems =  [];
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    updateWorkflows: function (request) {
      let component = this;
      this.loading = true;
      axios.post('api/requests/update_workflows', request).then(() => {
        component.fetchObjects();
      }).catch(error => {
        component.loading = false;
        component.clearDialog();
        component.showError("Error updating request info", component.getError(error));
      });
    },
    updateWorkflowsMany: function(requests) {
      let component = this;
      this.loading = true;
      axios.post('api/requests/update_workflows', requests.slice()).then(() => {
        component.fetchObjects();
        component.selectedItems =  [];
      }).catch(error => {
        component.loading = false;
        component.clearDialog();
        component.showError("Error updating request info", component.getError(error));
        component.selectedItems =  [];
      });
    },
    optionReset: function(request) {
      let component = this;
      this.dialog.title = "Option reset " + request.prepid + "?";
      this.dialog.description = "Are you sure you want to rewrite " + request.prepid + " memory, sequences and energy from " + request.subcampaign + "?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.post('api/requests/option_reset', request).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error option resetting request", component.getError(error));
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    optionResetMany: function(requests) {
      let component = this;
      this.dialog.title = "Option reset " + requests.length + " requests?";
      this.dialog.description = "Are you sure you want to rewrite memory, sequences, energy and CMSSW release for " + requests.length + " requests from their subcampaigns?";
      this.dialog.ok = function() {
        component.loading = true;
        axios.post('api/requests/option_reset', requests.slice()).then(() => {
          component.clearDialog();
          component.fetchObjects();
        }).catch(error => {
          component.loading = false;
          component.clearDialog();
          component.showError("Error option resetting requests", component.getError(error));
        });
      }
      this.dialog.cancel = function() {
        component.clearDialog();
      }
      this.dialog.visible = true;
    },
    openPmpMany: function(requests) {
      let prepids = requests.map(x => x['prepid']);
      let url = 'https://cms-pdmv.cern.ch/pmp/historical?r=' + prepids.join(',');
      window.open(url, '_blank');
    },
    editRequests: function(requests) {
      let prepids = requests.map(x => x['prepid']);
      window.location = 'requests/edit_many?prepid=' + prepids.join(',');
    },
    createTicket: function(requests) {
      let prepids = requests.map(x => x['prepid']);
      window.location = 'tickets/edit?input_requests=' + prepids.join(',');
    },
    sequenceSteps: function(sequence) {
      return sequence.step.map(x => x.split(':')[0]).join(',')
    }
  }
}
</script>

<style scoped>

.bar {
  line-height:10px;
  height: 10px;
  display: inline-block;
  max-width: 100%;
  background-color: #2C3E50;
}

.production-bar {
  background-color:#F39C12;
}

.valid-bar {
  background-color:#3498db;
}

.invalid-bar {
  background-color:#C0392B;
}

.deleted-bar {
  background-color:#E74C3C;
}

.gray-bar {
  width: 100px;
  background-color: #BDC3C7;
  display: inline-block;
  line-height:10px;
  height: 10px;
  font-size: 0;
  overflow: hidden;
  margin-right: 4px;
}

.valid-type {
  color: green;
}

.production-type, .invalid-type, .deleted-type, .deprecated-type {
  color: red;
}

.none-type {
  color: #8A8A8A;
}

.zebra-datasets > li:nth-child(2n) > div {
  background: #f5f5fc;
  background: linear-gradient(90deg, #f5f5fc 0%, rgba(0,212,255,0) 100%);
  padding-left: 24px;
  margin-left: -24px;
}

</style>