<template>
  <table class="history">
    <tr>
      <th>Time</th>
      <th>User</th>
      <th>Action</th>
      <th>Value</th>
    </tr>
    <tr v-for="entry in data" :key="entry.time">
      <td>{{entry.time}}</td>
      <td>{{entry.user}}</td>
      <td>{{entry.action}}</td>
      <td v-if="entry.action !== 'update'" style="max-width: 200px;">{{entry.value}}</td>
      <td v-if="entry.action === 'update'" style="max-width: 200px;">
        <ul>
          <li v-for="(value, attribute) in entry.value">
            {{attribute}}
          </li>
        </ul>
      </td>
    </tr>
  </table>
</template>

<script>
  export default {
    props:{
      data: {
        type: Array
      }
    },
    data () {
      return {
      }
    },
    created () {
    },
    watch:{
    },
    methods: {
    }
  }
</script>

<style scoped>

.history, .history td, .history th {
  border: 1px solid rgba(0, 0, 0, 0.87) !important;
  border-collapse: collapse;
  padding: 4px !important;
}

.history {
  margin-top: 4px;
  margin-bottom: 4px;
}

tr {
  height: 14px !important;
}

td {
  height: 14px !important;
}

</style>