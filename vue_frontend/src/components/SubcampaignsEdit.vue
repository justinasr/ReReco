<template>
  <div>
    <h1 v-if="creatingNew">Creating new Subcampaign</h1>
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
          <td>CMSSW Release</td>
          <td><input type="text" v-model="editableObject.cmssw_release" :disabled="!editingInfo.cmssw_release"></td>
        </tr>
        <tr>
          <td>SCRAM Arch</td>
          <td><input type="text" v-model="editableObject.scram_arch" :disabled="!editingInfo.scram_arch"></td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Sequences ({{listLength(editableObject.sequences)}})</td>
          <td>
            <div v-for="(sequence, index) in editableObject.sequences" :key="index">
              <h3>Sequence {{index + 1}}</h3>
              <table>
                <tr>
                  <td>conditions</td><td><input type="text" v-model="sequence.conditions" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>customise</td><td><input type="text" v-model="sequence.customise" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>datatier</td><td><input type="text" v-model="sequence.datatier" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>era</td><td><input type="text" v-model="sequence.era" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>eventcontent</td><td><input type="text" v-model="sequence.eventcontent" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>extra</td><td><input type="text" v-model="sequence.extra" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>nThreads</td><td><input type="number" v-model="sequence.nThreads" :disabled="!editableObject.sequences"></td>
                </tr>
                <tr>
                  <td>scenario</td>
                  <td>
                    <select v-model="sequence.scenario" :disabled="!editableObject.sequences">
                      <option>pp</option>
                      <option>cosmics</option>
                      <option>nocoll</option>
                      <option>HeavyIons</option>
                    </select>
                  </td>
                </tr>
                <tr>
                  <td>step</td><td><input type="text" v-model="sequence.step" :disabled="!editableObject.sequences"></td>
                </tr>
              </table>
              <v-btn small class="mr-1 mb-1" color="error" @click="deleteSequence(index)">Delete sequence {{index + 1}}</v-btn>
              <hr>
            </div>
            <v-btn small class="mr-1 mb-1 mt-1" color="primary" @click="addSequence()">Add sequence {{listLength(editableObject.sequences) + 1}}</v-btn>
          </td>
        </tr>
        <tr>
          <td>Memory</td>
          <td><input type="number" v-model="editableObject.memory" :disabled="!editingInfo.memory">MB</td>
        </tr>
        <tr>
          <td>Runs JSON</td>
          <td style="white-space: break-spaces; line-break: anywhere;">Get a list of runs from JSON, for example:<br>
            <span style="font-family: monospace;">Collisions16/13TeV/DCSOnly/json_DCSONLY.txt</span>
            <input type="text" v-model="editableObject.runs_json_path" :disabled="!editingInfo.runs_json_path">
          </td>
        </tr>
      </table>
      <v-btn small class="mr-1 mb-1" color="primary" @click="save()">Save</v-btn>
    </v-card>
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
import { listLengthMixin } from '../mixins/ListLengthMixin.js'

export default {
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
    axios.get('api/subcampaigns/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      component.editableObject = response.data.response.object;
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
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/subcampaigns/create', editableObject)
      } else {
        httpRequest = axios.post('api/subcampaigns/update', editableObject)
      }
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'subcampaigns?prepid=' + response.data.response.prepid;
      }).catch(error => {
        component.loading = false;
        this.showError('Error saving subcampaign', error.response.data.message);
      });
    },
    addSequence: function() {
      let component = this;
      axios.get('api/subcampaigns/get_default_sequence' + (this.creatingNew ? '' : ('/' + this.editableObject.subcampaign))).then(response => {
        component.editableObject['sequences'].push(response.data.response);
      });
    },
    deleteSequence: function(index) {
      this.editableObject['sequences'].splice(index, 1);
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