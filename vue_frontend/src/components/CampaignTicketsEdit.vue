<template>
  <div>
    <h1>Campaign Tickets Edit</h1>
    <v-card raised style="margin: auto; padding: 16px; max-width: 750px;">
      <table v-if="editableObject">
        <tr>
          <td>PrepID</td>
          <td><input v-model="editableObject.prepid" :disabled="!editingInfo.prepid"></td>
        </tr>
        <tr>
          <td>Campaign</td>
          <td><input v-model="editableObject.campaign" :disabled="!editingInfo.campaign"></td>
        </tr>
        <tr>
          <td>Processing String</td>
          <td><input v-model="editableObject.processing_string" :disabled="!editingInfo.processing_string"></td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><textarea v-model="editableObject.notes" :disabled="!editingInfo.notes"></textarea></td>
        </tr>
        <tr>
          <td>Input Datasets</td>
          <td><textarea v-model="editableObject.input_datasets" :disabled="!editingInfo.input_datasets"></textarea></td>
        </tr>
      </table>
      <v-btn @click="getDatasetsDialogVisible = true">Get dataset list from DBS</v-btn>
      <v-btn @click="save()">Save</v-btn>
    </v-card>
    <v-dialog v-model="getDatasetsDialogVisible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">Get dataset list</v-card-title>
        <v-card-text>
          Automatically get a list of input datasets from DBS. Enter dataset name query, for example <pre>/ZeroBias/*/RAW</pre>
          <input v-model="getDatasetsDialogInput">
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn :disabled="!getDatasetsDialogInput.length" @click="getDatasets()">OK</v-btn>
          <v-btn @click="getDatasetsDialogVisible = false; getDatasetsDialogInput = ''">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
      creatingNew: true,
      getDatasetsDialogVisible: false,
      getDatasetsDialogInput: ''
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
    axios.get('api/campaign_tickets/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
      console.log(response.data);
      component.editableObject = response.data.response.object;
      component.editableObject.sequences = JSON.stringify(component.editableObject.sequences, null, 4);
      component.editableObject.input_datasets = component.editableObject.input_datasets.filter(Boolean).join('\n')
      component.editingInfo = response.data.response.editing_info;
      component.loading = false;
    });
  },
  methods: {
    save: function() {
      console.log('Saving ' + this.prepid)
      let editableObject = JSON.parse(JSON.stringify(this.editableObject))
      this.loading = true;
      let component = this;
      editableObject['notes'] = editableObject['notes'].trim();
      editableObject['input_datasets'] = editableObject['input_datasets'].split('\n').map(function(s) { return s.trim() }).filter(Boolean);
      console.log(editableObject);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/campaign_tickets/create', editableObject)
      } else {
        httpRequest = axios.post('api/campaign_tickets/update', editableObject)
      }
      httpRequest.then(response => {
        console.log(response.data.response.prepid);
        component.loading = false;
        window.location = 'campaign_tickets?prepid=' + response.data.response.prepid;
      }).catch(error => {
        console.log('Error!');
        alert(error.response.data.message);
        console.log(error.response.data);
      });
    },
    getDatasets: function() {
      let component = this;
      console.log(this.getDatasetsDialogInput);
      let httpRequest = axios.get('api/campaign_tickets/get_datasets?q=' + this.getDatasetsDialogInput)
      httpRequest.then(response => {
        console.log(response.data.response.prepid);
        component.editableObject['input_datasets'] = response.data.response.filter(Boolean).join('\n');
        component.getDatasetsDialogVisible = false;
        component.getDatasetsDialogInput = '';
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

h1 {
  margin: 8px;
}

</style>