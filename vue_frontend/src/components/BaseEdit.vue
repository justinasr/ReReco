<template>
  <div>
    <slot/>
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

export default {
  name: 'BaseEdit',

  data () {
    return {
      prepid: undefined,
      databaseName: undefined,
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
  methods: {
    fetchEditable: function() {
      this.loading = true;
      let query = Object.assign({}, this.$route.query);
      this.prepid = query['prepid'];
      this.creatingNew = this.prepid === undefined;
      let component = this;
      axios.get('api/' + this.databaseName + '/get_editable' + (this.creatingNew ? '' : ('/' + this.prepid))).then(response => {
        component.editableObject = response.data.response.object;
        component.editableObject.input_datasets = component.editableObject.input_datasets.filter(Boolean).join('\n')
        component.editingInfo = response.data.response.editing_info;
        component.loading = false;
      });
    },
    baseSave: function(editableObject) {
      let component = this;
      editableObject['notes'] = editableObject['notes'].trim();
      let httpRequest;
      this.loading = true;
      if (this.creatingNew) {
        httpRequest = axios.put('api/' + this.databaseName + '/create', editableObject)
      } else {
        httpRequest = axios.post('api/' + this.databaseName + '/update', editableObject)
      }
      httpRequest.then(response => {
        component.loading = false;
        window.location = this.databaseName + '?prepid=' + response.data.response.prepid;
      }).catch(error => {
        component.loading = false;
        component.showError('Error saving ', error.response.data.message)
      });
    },
    clearErrorDialog: function() {
      this.errorDialog.visible = false;
      this.errorDialog.title = '';
      this.errorDialog.description = '';
    },
    showError: function(title, description) {
      this.clearErrorDialog();
      let lastChild = this.$children[this.$children.length - 1];
      console.log(this)
      console.log(lastChild);
      lastChild.errorDialog.title = title;
      lastChild.errorDialog.description = description;
      lastChild.errorDialog.visible = true;
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

.editPageCard {
  margin: auto;
  padding: 16px;
  max-width: 750px;
}

</style>