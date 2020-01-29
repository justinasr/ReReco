<template>
  <div class="subcampaigns">
    <h1>Home</h1>
    <div style="margin: 8px">
      <h3>ReReco objects:</h3>
      <ul>
        <li><a :href="'subcampaigns'">Subcampaigns</a></li>
        <li><a :href="'subcampaign_tickets'">Subcampaign tickets</a></li>
        <li><a :href="'requests'">Requests</a></li>
      </ul>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
// import HelloWorld from '@/components/HelloWorld.vue'

export default {
  name: 'home',
  components: {
    // HelloWorld
  }
}
</script>

<style scoped>

h1 {
  margin: 8px;
}

</style>
