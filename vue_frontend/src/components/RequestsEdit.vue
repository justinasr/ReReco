<template>
  <div>
    <h1 v-if="creatingNew">Creating new Request</h1>
    <h1 v-else>Editing {{editableObject.prepid}}</h1>
    <v-card raised style="margin: auto; padding: 16px; max-width: 750px;">
      <table v-if="editableObject">
        <tr>
          <td>PrepID</td>
          <td><input type="text" v-model="editableObject.prepid" :disabled="!editingInfo.prepid"></td>
        </tr>
        <tr>
          <td>Energy</td>
          <td><input type="number" v-model="editableObject.energy" :disabled="!editingInfo.energy">TeV</td>
        </tr>
        <tr>
          <td>CMSSW Version</td>
          <td><input type="text" v-model="editableObject.cmssw_release" :disabled="!editingInfo.cmssw_release"></td>
        </tr>
        <tr>
          <td>Subcampaign</td>
          <td><input type="text" v-model="editableObject.subcampaign" :disabled="!editingInfo.subcampaign"></td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Sequences</td>
          <td>
            <ul>
              <li v-for="(sequence, index) in editableObject.sequences" :key="index">
                Sequence {{index + 1}}
                <v-btn v-if="editingInfo.sequences" small class="mr-1 mb-1" color="primary" @click="showSequenceDialog(index, true)">Edit</v-btn>
                <v-btn v-if="editingInfo.sequences" small class="mr-1 mb-1" color="error" @click="deleteSequence(index)">Delete</v-btn>
                <v-btn v-if="!editingInfo.sequences" small class="mr-1 mb-1" color="primary" @click="showSequenceDialog(index, false)">View</v-btn>
              </li>
              <li v-if="editingInfo.sequences">
                <v-btn small class="mr-1 mb-1" color="primary" @click="showSequenceDialog(-1, true)">Add sequence</v-btn>
              </li>
            </ul>
          </td>
        </tr>
        <tr>
          <td>Memory</td>
          <td><input type="number" v-model="editableObject.memory" :disabled="!editingInfo.memory">MB</td>
        </tr>
        <tr>
          <td>Step</td>
          <td>
            <select v-model="editableObject.step" :disabled="!editingInfo.step">
              <option>DR</option>
              <option>MiniAOD</option>
              <option>NanoAOD</option>
            </select>
          </td>
        </tr>
        <tr>
          <td>Input dataset</td>
          <td><input type="text" v-model="editableObject.input_dataset" :disabled="!editingInfo.input_dataset"></td>
        </tr>
        <tr>
          <td>Priority</td>
          <td><input type="number" v-model="editableObject.priority" :disabled="!editingInfo.priority"></td>
        </tr>
        <tr>
          <td>Processing String</td>
          <td><input type="text" v-model="editableObject.processing_string" :disabled="!editingInfo.processing_string"></td>
        </tr>
        <tr>
          <td>Runs ({{listLength(editableObject.runs)}})</td>
          <td><textarea v-model="editableObject.runs" :disabled="!editingInfo.runs"></textarea></td>
        </tr>
        <tr>
          <td>Size per event</td>
          <td><input type="number" v-model="editableObject.size_per_event" :disabled="!editingInfo.size_per_event">kB</td>
        </tr>
        <tr>
          <td>Time per event</td>
          <td><input type="number" v-model="editableObject.time_per_event" :disabled="!editingInfo.time_per_event">s</td>
        </tr>
      </table>
      <v-btn small class="mr-1 mb-1" color="primary" @click="save()">Save</v-btn>
      <v-btn v-if="editingInfo.runs && !creatingNew" small class="mr-1 mb-1" color="primary" @click="getRuns()">Get runs from DBS and certification</v-btn>
    </v-card>
    <v-dialog v-model="sequenceEditDialog.visible"
              max-width="50%">
      <v-card style="padding: 16px;">
        <SequencesEdit :sequenceObject="sequenceEditDialog.sequence"
                       :sequenceIndex="sequenceEditDialog.index"
                       :editable="sequenceEditDialog.editable"
                       v-on:saveSequence="onSeqenceSave"/>
      </v-card>
    </v-dialog>
    <v-overlay :absolute="false"
               :opacity="0.95"
               :z-index="3"
               :value="loading"
               style="text-align: center">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <br>Please wait...
    </v-overlay>
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
          <v-btn small class="mr-1 mb-1" color="primary" @click="clearErrorDialog()">
            Dismiss
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>

import axios from 'axios'
import SequencesEdit from './SequencesEdit'
import { listLengthMixin } from '../mixins/ListLengthMixin.js'

export default {
  components: {
    SequencesEdit
  },
  mixins: [
    listLengthMixin
  ],
  data () {
    return {
      prepid: undefined,
      editableObject: {},
      editingInfo: {},
      loading: true,
      creatingNew: true,
      sequenceEditDialog: {
        visible: false,
        index: -1,
        sequence: undefined,
        editable: false,
      },
      errorDialog: {
        visible: false,
        title: '',
        description: '',
      }
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    this.prepid = query['prepid'];
    this.creatingNew = this.prepid === undefined;
    this.loading = true;
    let component = this;
    axios.get('api/requests/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      component.editableObject = response.data.response.object;
      // component.editableObject.sequences = JSON.stringify(component.editableObject.sequences, null, 2);
      component.editableObject.runs = component.editableObject.runs.join('\n')
      component.editingInfo = response.data.response.editing_info;
      component.loading = false;
    });
  },
  methods: {
    save: function() {
      this.loading = true;
      let editableObject = JSON.parse(JSON.stringify(this.editableObject))
      let component = this;
      editableObject['notes'] = editableObject['notes'].trim();
      editableObject['runs'] = editableObject['runs'].replace(/,/g, '\n').split('\n').map(function(s) { return s.trim() }).filter(Boolean);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/requests/create', editableObject)
      } else {
        httpRequest = axios.post('api/requests/update', editableObject)
      }
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'requests?prepid=' + response.data.response.prepid;
      }).catch(error => {
        this.showError('Error saving request', error.response.data.message);
        component.loading = false;
      });
    },
    showSequenceDialog: function(index, editable) {
      if (index < 0) {
        let component = this;
        axios.get('api/subcampaigns/get_default_sequence' + (this.creatingNew ? '' : ('/' + this.editableObject.subcampaign))).then(response => {
          component.sequenceEditDialog.visible = true;
          component.sequenceEditDialog.index = index;
          component.sequenceEditDialog.sequence = response.data.response;
          component.sequenceEditDialog.editable = editable;
        });
      } else {
        this.sequenceEditDialog.visible = true;
        this.sequenceEditDialog.index = index;
        this.sequenceEditDialog.sequence = this.editableObject.sequences[index];
        this.sequenceEditDialog.editable = editable;
      }
    },
    onSeqenceSave: function(index, sequence) {
      if (index < 0) {
        this.editableObject['sequences'].push(sequence);
      } else {
        this.editableObject['sequences'][index] = sequence;
      }
      this.sequenceEditDialog.visible = false;
    },
    deleteSequence: function(index) {
      this.editableObject['sequences'].splice(index, 1);
    },
    getRuns: function() {
      let component = this;
      this.loading = true;
      axios.get('api/requests/get_runs/' + this.prepid).then(response => {
        component.editableObject.runs = response.data.response.filter(Boolean).map(function(s) { return s.toString() }).join('\n');
        this.loading = false;
      }).catch(error => {
        this.showError('Error getting runs for request', error.response.data.message)
        component.loading = false;
      });
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
    }
  }
}
</script>

<style scoped>

h1 {
  margin: 8px;
}

td {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-right: 4px;
}

</style>