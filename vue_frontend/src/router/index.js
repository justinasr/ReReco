import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/components/Home'
import Subcampaigns from '@/components/Subcampaigns'
import SubcampaignTickets from '@/components/SubcampaignTickets'
import SubcampaignTicketsEdit from '@/components/SubcampaignTicketsEdit'
import SubcampaignsEdit from '@/components/SubcampaignsEdit'
import Flows from '@/components/Flows'
import ChainedCampaigns from '@/components/ChainedCampaigns'
import ChainedRequests from '@/components/ChainedRequests'
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
    path: '/subcampaign_tickets/edit',
    name: 'subcampaign_tickets_edit',
    component: SubcampaignTicketsEdit
  },
  {
    path: '/subcampaign_tickets',
    name: 'subcampaign_tickets',
    component: SubcampaignTickets
  },
  {
    path: '/flows',
    name: 'flows',
    component: Flows
  },
  {
    path: '/chained_campaigns',
    name: 'chained_campaigns',
    component: ChainedCampaigns
  },
  {
    path: '/chained_requests',
    name: 'chained_requests',
    component: ChainedRequests
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
    result = result.replace(/%2A/g, '*').replace(/%2F/g, '/').replace(/%21/g, '!');
    return result ? ('?' + result) : '';
  },
  routes
})

export default router
