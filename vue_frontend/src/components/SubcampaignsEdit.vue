<template>
  <div>
    <h1 class="page-title" v-if="creatingNew"><span class="font-weight-light">Creating</span> new subcampaign</h1>
    <h1 class="page-title" v-else><span class="font-weight-light">Editing</span> {{prepid}}</h1>
    <v-card raised class="page-card">
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
          <td><input type="text" v-model="editableObject.runs_json_path" :disabled="!editingInfo.runs_json_path" placeholder="Example: Collisions16/13TeV/DCSOnly/json_DCSONLY.txt"></td>
        </tr>
      </table>
      <v-btn small class="mr-1 mt-2" color="primary" @click="save()">Save</v-btn>
    </v-card>
    <LoadingOverlay :visible="loading"/>
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
import { utilsMixin } from '../mixins/UtilsMixin.js'
import LoadingOverlay from './LoadingOverlay.vue'

export default {
  mixins: [
    utilsMixin
  ],
  components: {
    LoadingOverlay
  },
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
    if (query.prepid && query.prepid.length) {
      this.prepid = query.prepid;
    } else {
      this.prepid = '';
    }
    this.creatingNew = this.prepid.length == 0;
    this.loading = true;
    let component = this;
    axios.get('api/subcampaigns/get_editable/' + this.prepid).then(response => {
      component.editableObject = response.data.response.object;
      component.editingInfo = response.data.response.editing_info;
      component.loading = false;
    }).catch(error => {
      component.loading = false;
      this.showError('Error fetching editing information', error.response.data.message);
    });
  },
  methods: {
    save: function() {
      this.loading = true;
      let editableObject = this.makeCopy(this.editableObject);
      editableObject.notes = editableObject.notes.trim();
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/subcampaigns/create', editableObject);
      } else {
        httpRequest = axios.post('api/subcampaigns/update', editableObject);
      }
      let component = this;
      httpRequest.then(response => {
        component.loading = false;
        window.location = 'subcampaigns?prepid=' + response.data.response.prepid;
      }).catch(error => {
        component.loading = false;
        this.showError('Error saving subcampaign', error.response.data.message);
      });
    },
    addSequence: function() {
      this.loading = true;
      let component = this;
      axios.get('api/subcampaigns/get_default_sequence/' + this.editableObject.subcampaign).then(response => {
        component.editableObject.sequences.push(response.data.response);
        component.loading = false;
      }).catch(error => {
        component.loading = false;
        this.showError('Error getting sequence information', error.response.data.message);
      });
    },
    deleteSequence: function(index) {
      this.editableObject.sequences.splice(index, 1);
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