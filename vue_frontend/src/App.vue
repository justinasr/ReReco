<template>
  <v-app>
    <v-app-bar app>
      <a href="" style="text-decoration: none; color: rgba(0, 0, 0, 0.87);">
        <v-toolbar-title class="headline">
          <span>Re</span>
          <span class="font-weight-light">Reco</span>
        </v-toolbar-title>
      </a>
      <v-spacer></v-spacer>
      <v-btn
        text
        href="campaigns">
        <span class="mr-2">Campaigns</span>
      </v-btn>
      <v-btn
        text
        href="campaign_tickets">
        <span class="mr-2">Campaign Tickets</span>
      </v-btn>
<!--       <v-btn
        text
        href="flows">
        <span class="mr-2">Flows</span>
      </v-btn>
      <v-btn
        text
        href="chained_campaigns">
        <span class="mr-2">Chained Campaigns</span>
      </v-btn>
      <v-btn
        text
        href="chained_requests">
        <span class="mr-2">Chained Requests</span>
      </v-btn> -->
      <v-btn
        text
        href="requests">
        <span class="mr-2">Requests</span>
      </v-btn>
    </v-app-bar>
    <v-content>
       <router-view/>
    </v-content>
  </v-app>
</template>

<script>

export default {
  name: 'App',

  components: {
  },

  data: () => ({
    //
  }),
};
</script>

<style>

footer {
  height: 56px;
  left: 0px;
  right: 0px;
  bottom: 0px;
  position: fixed;
  background-color: white;
  box-shadow: 0px -2px 4px -1px rgba(0, 0, 0, 0.2), 0px -4px 5px 0px rgba(0, 0, 0, 0.14), 0px -1px 10px 0px rgba(0, 0, 0, 0.12);
}

.v-content__wrap > div {
  padding-bottom: 72px;
}

.notes {
  font-size: 0.85em;
  margin: 4px;
  padding: 4px;
  border: 1px solid rgba(0, 0, 0, 0.5);
}

</style>