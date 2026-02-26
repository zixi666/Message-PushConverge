import request from './request'

// 获取渠道列表
export function listWays(params) {
  return request({
    url: '/sendways/list',
    method: 'get',
    params
  })
}

// 添加渠道
export function addWay(data) {
  return request({
    url: '/sendways/add',
    method: 'post',
    data
  })
}

// 编辑渠道
export function editWay(id, data) {
  return request({
    url: '/sendways/edit',
    method: 'post',
    params: { id },
    data
  })
}

// 删除渠道
export function deleteWay(id) {
  return request({
    url: '/sendways/delete',
    method: 'post',
    params: { id }
  })
}

// 测试渠道
export function testWay(id) {
  return request({
    url: '/sendways/test',
    method: 'post',
    params: { id }
  })
}

// 获取渠道详情
export function getWay(id) {
  return request({
    url: '/sendways/get',
    method: 'get',
    params: { id }
  })
}