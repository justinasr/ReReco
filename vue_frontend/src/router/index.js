import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/components/Home'
import Campaigns from '@/components/Campaigns'
import CampaignsEdit from '@/components/CampaignsEdit'
import Flows from '@/components/Flows'
import ChainedCampaigns from '@/components/ChainedCampaigns'
import ChainedRequests from '@/components/ChainedRequests'
import Requests from '@/components/Requests'


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
    path: '/requests',
    name: 'requests',
    component: Requests
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
