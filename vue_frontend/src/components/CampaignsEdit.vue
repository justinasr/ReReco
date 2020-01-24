<template>
  <div>
    <h1>Campaigns Edit</h1>
    <v-card raised style="margin: auto; padding: 16px; max-width: 750px;">
      <table v-if="editableObject">
        <tr>
          <td>PrepID</td>
          <td><input v-model="editableObject.prepid" :disabled="!editingInfo.prepid"></td>
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
          <td><input v-model="editableObject.cmssw_release" :disabled="!editingInfo.cmssw_release"></td>
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
                <v-btn @click="showSequenceDialog(index)">Edit</v-btn>
                <v-btn @click="deleteSequence(index)">Delete</v-btn>
              </li>
              <li>
                <v-btn @click="showSequenceDialog(-1)">Add new sequence</v-btn>
              </li>
            </ul>
          </td>
        </tr>
        <tr>
          <td>Memory</td>
          <td><input type="number" v-model="editableObject.memory" :disabled="!editingInfo.memory">MB</td>
        </tr>
      </table>
      <v-btn @click="save()">Save</v-btn>
    </v-card>
    <v-dialog v-model="sequenceEditDialog.visible"
              max-width="50%">
      <v-card style="padding: 16px;">
        <SequencesEdit :sequenceObject="sequenceEditDialog.sequence"
                       :sequenceIndex="sequenceEditDialog.index"
                       v-on:saveSequence="onSeqenceSave"/>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>

import axios from 'axios'
import SequencesEdit from './SequencesEdit'

export default {
  components: {
    SequencesEdit
  },
  data () {
    return {
      prepid: undefined,
      editableObject: undefined,
      editingInfo: undefined,
      loading: true,
      creatingNew: true,
      sequenceEditDialog: {
        visible: false,
        index: -1,
        sequence: undefined
      }
    }
  },
  computed: {
  },
  watch: {
    editableObject: {
      handler: function() {
        console.log('Something changed')
      },
      deep: true
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    this.prepid = query['prepid'];
    this.creatingNew = this.prepid === undefined;
    this.loading = true;
    let component = this;
    axios.get('api/campaigns/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      console.log(response.data);
      component.editableObject = response.data.response.object;
      // component.editableObject.sequences = JSON.stringify(component.editableObject.sequences, null, 4);
      component.editingInfo = response.data.response.editing_info;
      component.loading = false;
    });
  },
  methods: {
    save: function() {
      console.log('Saving ' + this.prepid)
      this.loading = true;
      let editableObject = JSON.parse(JSON.stringify(this.editableObject))
      let component = this;
      editableObject['notes'] = editableObject['notes'].trim();
      console.log(this.editableObject);
      // editableObject['sequences'] = JSON.parse(editableObject['sequences']);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/campaigns/create', editableObject)
      } else {
        httpRequest = axios.post('api/campaigns/update', editableObject)
      }
      httpRequest.then(response => {
        console.log(response.data.response.prepid);
        component.loading = false;
        window.location = 'campaigns?prepid=' + response.data.response.prepid;
      }).catch(error => {
        console.log('Error!');
        component.loading = false;
        alert(error.response.data.message);
        console.log(error.response.data);
      });
    },
    showSequenceDialog: function(index) {
      if (index < 0) {
        let component = this;
        axios.get('api/campaigns/get_default_sequence' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
          component.sequenceEditDialog.visible = true;
          component.sequenceEditDialog.index = index;
          component.sequenceEditDialog.sequence = response.data.response;
        });
      } else {
        this.sequenceEditDialog.visible = true;
        this.sequenceEditDialog.index = index;
        this.sequenceEditDialog.sequence = this.editableObject.sequences[index];
      }
    },
    onSeqenceSave: function(index, sequence) {
      console.log('Saving ' + index + ' sequence');
      if (index < 0) {
        this.editableObject['sequences'].push(sequence);
      } else {
        this.editableObject['sequences'][index] = sequence;
      }
      this.sequenceEditDialog.visible = false;
    },
    deleteSequence: function(index) {
      console.log('Deleting ' + index + ' sequence');
      this.editableObject['sequences'].splice(index, 1);
    }
  }
}
</script>

<style scoped>

input, select, textarea {
  border-style: inset;
  background-color: inherit;
  -webkit-appearance: auto;
  min-width: 500px;
}

textarea {
  min-height: 500px;
  font-family: monospace;
  font-size: 0.8em;
}

h1 {
  margin: 8px;
}

</style>