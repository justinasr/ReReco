<template>
  <div>
    <h1>CampaignsEdit</h1>
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
        <td>Type</td>
        <td><input v-model="editableObject.type" :disabled="!editingInfo.type"></td>
      </tr>
      <tr>
        <td>CMSSW Version</td>
        <td><input v-model="editableObject.cmssw_version" :disabled="!editingInfo.cmssw_version"></td>
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
    </table>
    <v-btn @click="save()">Save</v-btn>
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
    axios.get('api/campaigns/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      console.log(response.data);
      component.editableObject = response.data.response.object;
      component.editableObject.sequences = JSON.stringify(component.editableObject.sequences, null, 4);
      component.editingInfo = response.data.response.editing_info;
      component.loading = false;
    });
  },
  methods: {
    save: function() {
      console.log('Saving ' + this.prepid)
      this.loading = true;
      let component = this;
      this.editableObject['notes'] = this.editableObject['notes'].trim();
      console.log(this.editableObject);
      this.editableObject['sequences'] = JSON.parse(this.editableObject['sequences']);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/campaigns/create', this.editableObject)
      } else {
        httpRequest = axios.post('api/campaigns/update', this.editableObject)
      }
      httpRequest.then(response => {
        console.log(response.data.response.prepid);
        component.loading = false;
        window.location = 'campaigns?prepid=' + response.data.response.prepid;
      }).catch(error => {
        console.log('Error!');
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

</style>