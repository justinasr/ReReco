<template>
  <div>
    <h1>Requests Edit</h1>
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
          <td>CMSSW Version</td>
          <td><input v-model="editableObject.cmssw_release" :disabled="!editingInfo.cmssw_release"></td>
        </tr>
        <tr>
          <td>Campaign</td>
          <td><input v-model="editableObject.member_of_campaign" :disabled="!editingInfo.member_of_campaign"></td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Sequences</td>
          <td><textarea v-model="editableObject.sequences" :disabled="!editingInfo.sequences"></textarea></td>
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
          <td><input v-model="editableObject.input_dataset" :disabled="!editingInfo.input_dataset"></td>
        </tr>
        <tr>
          <td>Priority</td>
          <td><input type="number" v-model="editableObject.priority" :disabled="!editingInfo.priority"></td>
        </tr>
        <tr>
          <td>Processing String</td>
          <td><input v-model="editableObject.processing_string" :disabled="!editingInfo.processing_string"></td>
        </tr>
        <tr>
          <td>Runs</td>
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
      <v-btn @click="save()">Save</v-btn>
    </v-card>
  </div>
</template>

<script>

import axios from 'axios'

export default {
  components: {

  },
  data () {
    return {
      prepid: undefined,
      editableObject: undefined,
      editingInfo: undefined,
      loading: true,
      creatingNew: true
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
    axios.get('api/requests/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      console.log(response.data);
      component.editableObject = response.data.response.object;
      component.editableObject.sequences = JSON.stringify(component.editableObject.sequences, null, 2);
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
      editableObject['sequences'] = JSON.parse(editableObject['sequences']);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/requests/create', editableObject)
      } else {
        httpRequest = axios.post('api/requests/update', editableObject)
      }
      httpRequest.then(response => {
        console.log(response.data.response.prepid);
        component.loading = false;
        window.location = 'requests?prepid=' + response.data.response.prepid;
      }).catch(error => {
        console.log('Error!');
        component.loading = false;
        alert(error.response.data.message);
        console.log(error.response.data);
      });
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