import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/components/Home'
import Subcampaigns from '@/components/Subcampaigns'
import Tickets from '@/components/Tickets'
import TicketsEdit from '@/components/TicketsEdit'
import SubcampaignsEdit from '@/components/SubcampaignsEdit'
import Requests from '@/components/Requests'
import RequestsEdit from '@/components/RequestsEdit'
import Dashboard from '@/components/Dashboard'
import qs from 'qs';


Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home
  },
  {
    path: '/subcampaigns/edit',
    name: 'subcampaigns_edit',
    component: SubcampaignsEdit
  },
  {
    path: '/subcampaigns',
    name: 'subcampaigns',
    component: Subcampaigns
  },
  {
    path: '/tickets/edit',
    name: 'tickets_edit',
    component: TicketsEdit
  },
  {
    path: '/tickets',
    name: 'tickets',
    component: Tickets
  },
  {
    path: '/requests/edit',
    name: 'requests_edit',
    component: RequestsEdit
  },
  {
    path: '/requests',
    name: 'requests',
    component: Requests
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  stringifyQuery: query => {
    var result = qs.stringify(query);
    // Do not encode asterisks
    result = result.replace(/%2A/g, '*').replace(/%2F/g, '/').replace(/%21/g, '!').replace(/%2C/g, ',');
    return result ? ('?' + result) : '';
  },
  routes
})

export default router
