<template>
  <div>
    <h1>Editing "{{sequenceIndex < 0 ? 'new' : sequenceIndex + 1}}" sequence</h1>
    <table>
      <tr v-for="(value, key) in editableObject" :key="key">
        <td>{{key}}</td><td><input v-model="editableObject[key]"></td>
      </tr>
    </table>
    <v-btn @click="save()">Save</v-btn>
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
    }
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

input, select, textarea {
  border-style: inset;
  background-color: inherit;
  -webkit-appearance: auto;
  min-width: 300px;
}

</style>