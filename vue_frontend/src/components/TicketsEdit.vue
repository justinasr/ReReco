<template>
  <BaseEdit>
    <h1 v-if="creatingNew">Creating new Ticket</h1>
    <h1 v-else>Editing ticket {{editableObject.prepid}}</h1>
    <v-card raised class="editPageCard">
      <table v-if="editableObject">
        <tr>
          <td>PrepID</td>
          <td><input type="text" v-model="editableObject.prepid" :disabled="!editingInfo.prepid"></td>
        </tr>
        <tr>
          <td>Steps ({{listLength(editableObject.steps)}})</td>
          <td>
            <div v-for="(step, index) in editableObject.steps" :key="index">
              <table v-if="index != 0">
                <tr>
                  <td>Submit</td>
                  <td>
                    <select v-model="step.join_type">
                      <option value="on_done">Step {{index + 1}} after Step {{index}} is done</option>
                      <option value="together">Step {{index + 1}} together with Step {{index}}</option>
                    </select>
                  </td>
                </tr>
              </table>
              <hr v-if="index != 0">
              <h3>Step {{index + 1}}</h3>
              <table>
                <tr>
                  <td>Subcampaign</td><td><input type="text" v-model="step.subcampaign" :disabled="!editingInfo.steps"></td>
                </tr>
                <tr>
                  <td>Processing String</td><td><input type="text" v-model="step.processing_string" :disabled="!editingInfo.steps"></td>
                </tr>
                <tr>
                  <td>Size per event</td><td><input type="number" v-model="step.size_per_event" :disabled="!editingInfo.steps">kB</td>
                </tr>
                <tr>
                  <td>Time per event</td><td><input type="number" v-model="step.time_per_event" :disabled="!editingInfo.steps">s</td>
                </tr>
                <tr>
                  <td>Priority</td><td><input type="number" v-model="step.priority" :disabled="!editingInfo.steps"></td>
                </tr>
              </table>
              <v-btn small class="mr-1 mb-1" color="error" @click="deleteStep(index)">Delete step {{index + 1}}</v-btn>
              <hr>
            </div>
            <v-btn small class="mr-1 mb-1 mt-1" color="primary" @click="addStep()">Add step {{listLength(editableObject.steps) + 1}}</v-btn>
          </td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Input Datasets ({{listLength(editableObject.input_datasets)}})</td>
          <td><textarea v-model="editableObject.input_datasets" :disabled="!editingInfo.input_datasets"></textarea></td>
        </tr>
      </table>
      <v-btn small class="mr-1 mb-1" color="primary" @click="save()">Save</v-btn>
      <v-btn v-if="editingInfo.input_datasets" small class="mr-1 mb-1" color="primary" @click="showGetDatasetsDialog()">Get dataset list from DBS</v-btn>
    </v-card>
    <v-dialog v-model="getDatasetsDialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">Get dataset list</v-card-title>
        <v-card-text>
          Automatically get a list of input datasets from DBS. Query must satisfy this format:<pre>/*/*/RAW</pre>Enter dataset name query below, for example:<pre>/ZeroBias/Run2018*/RAW</pre>
          <input type="text" v-model="getDatasetsDialog.input">
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" :disabled="!getDatasetsDialog.input.length" @click="getDatasets()">Get</v-btn>
          <v-btn small class="mr-1 mb-1" color="error" @click="closeGetDatasetsDialog()">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <LoadingOverlay :visible="loading"/>
  </BaseEdit>
</template>

<script>

import axios from 'axios'
import { listLengthMixin } from '../mixins/ListLengthMixin.js'
import BaseEdit from './BaseEdit.vue'
import LoadingOverlay from './LoadingOverlay.vue'

export default {
  extends: BaseEdit,

  name: 'TicketsEdit',
  components: {
    BaseEdit,
    LoadingOverlay
  },
  mixins: [
    listLengthMixin
  ],
  data () {
    return {
      databaseName: 'tickets',
      getDatasetsDialog: {
        visible: false,
        input: '',
      }
    }
  },
  created () {
    this.fetchEditable();
  },
  methods: {
    save: function() {
      let editableObject = JSON.parse(JSON.stringify(this.editableObject))
      editableObject['input_datasets'] = editableObject['input_datasets'].split('\n').map(function(s) { return s.trim() }).filter(Boolean);
      this.baseSave(editableObject);
    },
    getDatasets: function() {
      this.loading = true;
      let component = this;
      // Timeout 120000ms is 2 minutes
      let httpRequest = axios.get('api/tickets/get_datasets?q=' + this.getDatasetsDialog.input, {timeout: 120000});
      this.closeGetDatasetsDialog();
      httpRequest.then(response => {
        component.editableObject['input_datasets'] = response.data.response.filter(Boolean).join('\n');
        component.loading = false;
      }).catch(error => {
        this.showError('Error getting datasets for ticket', error.response.data.message)
        component.loading = false;
      });
    },
    showGetDatasetsDialog: function() {
      this.getDatasetsDialog.visible = true;
      this.getDatasetsDialog.input = '';
    },
    closeGetDatasetsDialog: function() {
      this.getDatasetsDialog.visible = false;
      this.getDatasetsDialog.input = '';
    },
    addStep: function() {
      this.editableObject['steps'].push({'join_type': 'on_done',
                                         'subcampaign': '',
                                         'processing_string': '',
                                         'priority': 110000,
                                         'size_per_event': 1.0,
                                         'time_per_event': 1.0});
    },
    deleteStep: function(index) {
      this.editableObject['steps'].splice(index, 1);
    }
  }
}
</script>

<style scoped>


</style>