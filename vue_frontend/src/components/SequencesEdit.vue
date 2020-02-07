<template>
  <div>
    <h1>{{editable ? 'Editing' : 'Viewing'}} "{{sequenceIndex < 0 ? 'new' : sequenceIndex + 1}}" sequence</h1>
    <table>
      <tr>
        <td>conditions</td><td><input type="text" v-model="editableObject.conditions" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>customise</td><td><input type="text" v-model="editableObject.customise" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>datatier</td><td><input type="text" v-model="editableObject.datatier" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>era</td><td><input type="text" v-model="editableObject.era" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>eventcontent</td><td><input type="text" v-model="editableObject.eventcontent" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>extra</td><td><input type="text" v-model="editableObject.extra" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>nThreads</td><td><input type="number" v-model="editableObject.nThreads" :disabled="!editable"></td>
      </tr>
      <tr>
        <td>scenario</td>
        <td>
          <select v-model="editableObject.scenario" :disabled="!editable">
            <option>pp</option>
            <option>cosmics</option>
            <option>nocoll</option>
            <option>HeavyIons</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>step</td><td><input type="text" v-model="editableObject.step" :disabled="!editable"></td>
      </tr>
    </table>
    <v-btn small class="mr-1 mb-1" color="primary" v-if="editable" @click="save()">Save</v-btn>
  </div>
</template>

<script>

export default {
  components: {

  },
  data () {
    return {
      editableObject: undefined,
    }
  },
  computed: {
  },
  watch: {
    sequenceObject: function (newValue, oldValue) {
      this.editableObject = this.sequenceObject;
    }
  },
  props:{
    sequenceObject: undefined,
    sequenceIndex: {
      type: Number,
      default: -1,
    },
    editable: false
  },
  created () {
    this.editableObject = this.sequenceObject;
  },
  methods: {
    save: function() {
      this.$emit('saveSequence', this.sequenceIndex, this.sequenceObject);
    }
  }
}
</script>

<style scoped>

td {
  padding-top: 8px;
  padding-bottom: 8px;
  padding-right: 4px;
}

</style>