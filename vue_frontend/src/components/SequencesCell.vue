<template>
    <ul>
      <li v-for="(sequence, index) in data" :key="index">
        Sequence {{index + 1}}:
        <ul>
          <li v-for="key in sequenceKeys(sequence)" :key="key" class="monospace">{{sequenceKey(key)}} {{sequenceValue(sequence[key])}}</li>
        </ul>
      </li>
    </ul>
</template>

<script>

  export default {
    props:{
      data: {
        type: Array
      }
    },
    methods: {
      sequenceKeys: function(sequence) {
        const ignore = ['config_id', 'harvesting_config_id', 'gpu'];
        return Object.keys(sequence).filter(s => sequence[s] != '' && sequence[s] !== false && !ignore.includes(s));
      },
      sequenceKey: function(key) {
        return key == 'extra' ? '' : ('--' + key);
      },
      sequenceValue: function(value) {
        if (Array.isArray(value)) {
          return value.join(',');
        }
        return value;
      }
    },
  }
</script>

<style scoped>

.monospace {
  font-family: monospace;
  font-size: 0.9em;
}

li {
  margin-bottom: -4px;
}

ul {
  margin-bottom: 4px;
}

</style>