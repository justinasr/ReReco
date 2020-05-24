<template>
  <v-app>
    <v-app-bar app style="background-color: white;">
      <a href="" style="text-decoration: none; color: rgba(0, 0, 0, 0.87);">
        <v-toolbar-title class="headline">
          <span>Re</span>
          <span class="font-weight-light">Reco</span>
        </v-toolbar-title>
      </a>
      <v-spacer></v-spacer>
      <v-btn
        text
        href="subcampaigns">
        <span class="mr-2">Subcampaigns</span>
      </v-btn>
      <v-btn
        text
        href="tickets">
        <span class="mr-2">Tickets</span>
      </v-btn>
      <v-btn
        text
        href="chained_requests">
        <span class="mr-2">Chained Requests</span>
      </v-btn>
      <v-btn
        text
        href="requests">
        <span class="mr-2">Requests</span>
      </v-btn>
      <v-btn
        text
        href="dashboard">
        <span class="mr-2">Dashboard</span>
      </v-btn>
      <v-spacer></v-spacer>
      <div v-if="userInfo" style="text-align: right; line-height: 28px;">
        <span :title="'Username: ' + userInfo.username + '\nRole: ' + userInfo.role"><small>Logged in as</small> {{userInfo.fullname}} </span>
        <img style="width: 16px; height: 16px;" v-if="userInfo.role_index == 1" src="static/star.png"/>
        <img style="width: 16px; height: 16px;" v-if="userInfo.role_index == 2" src="static/admin_star.png"/>
      </div>
    </v-app-bar>
    <v-content style="background-color: #fafafa;">
      <router-view/>
    </v-content>
  </v-app>
</template>

<script>

import { roleMixin } from './mixins/UserRoleMixin.js'

export default {
  name: 'App',

  mixins: [
    roleMixin
  ]
};
</script>

<style>

html {
  overflow: auto !important;
}

select, textarea {
  border-style: inset !important;
  min-width: 400px;
}

select {
  min-width: 200px;
}

input[type="number"] {
  border-style: inset !important;
  width: 100px;
  min-width: 100px;
  text-align: right;
}

input[type="text"] {
  border-style: inset !important;
  -webkit-appearance: textfield !important;
  min-width: 400px;
}

textarea {
  -webkit-appearance: textarea !important;
  min-height: 200px;
  font-family: monospace;
  font-size: 0.8em;
}

select {
  -webkit-appearance: menulist !important;
}

footer {
  height: 56px;
  left: 0px;
  right: 0px;
  bottom: 0px;
  position: fixed;
  background-color: white;
  box-shadow: 0px -2px 4px -1px rgba(0, 0, 0, 0.2), 0px -4px 5px 0px rgba(0, 0, 0, 0.14), 0px -1px 10px 0px rgba(0, 0, 0, 0.12);
}

table {
  white-space: nowrap;
}

.notes {
  font-size: 0.85em;
  margin: 4px;
  padding: 4px;
  border: 1px solid rgba(0, 0, 0, 0.5);
}

input:disabled, select:disabled, textarea:disabled {
  background: #dddddd !important;
  cursor: not-allowed;
}

.v-data-table__wrapper {
  overflow-x: visible !important;
  overflow-y: visible !important;
}

.mdi-checkbox-marked::before {
  color: var(--v-accent-base) !important
}

</style>