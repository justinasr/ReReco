import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/components/Home'
import Campaigns from '@/components/Campaigns'
import CampaignTickets from '@/components/CampaignTickets'
import CampaignTicketsEdit from '@/components/CampaignTicketsEdit'
import CampaignsEdit from '@/components/CampaignsEdit'
import Flows from '@/components/Flows'
import ChainedCampaigns from '@/components/ChainedCampaigns'
import ChainedRequests from '@/components/ChainedRequests'
import Requests from '@/components/Requests'
import RequestsEdit from '@/components/RequestsEdit'
import qs from 'qs';


Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home
  },
  {
    path: '/campaigns/edit',
    name: 'campaigns_edit',
    component: CampaignsEdit
  },
  {
    path: '/campaigns',
    name: 'campaigns',
    component: Campaigns
  },
  {
    path: '/campaign_tickets/edit',
    name: 'campaign_tickets_edit',
    component: CampaignTicketsEdit
  },
  {
    path: '/campaign_tickets',
    name: 'campaign_tickets',
    component: CampaignTickets
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
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  stringifyQuery: query => {
    var result = qs.stringify(query);
    // Do not encode asterisks
    result = result.replace(/%2A/g, '*');
    return result ? ('?' + result) : '';
  },
  routes
})

export default router
