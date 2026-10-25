import { randomUUID } from 'node:crypto';
import { expect, test } from '@playwright/test';
import { RoomManagementPage, type RoomForm } from '../pages/room-management.page';

function newRoom(): RoomForm {
  return {
    roomNo: `UI-RM-${randomUUID().slice(0, 8)}`,
    floor: 9,
    layout: '一房一厅',
    area: 35,
    status: '空置',
  };
}

test.describe('管理员房间管理', () => {
  test.beforeEach(async ({ page }) => {
    await new RoomManagementPage(page).open();
  });

  test('RM-001: 房间列表正常加载', async ({ page }) => {
    for (const name of ['公寓', '房间号', '楼层', '户型', '面积(㎡)', '状态', '更新时间', '操作']) {
      await expect(page.getByRole('columnheader', { name })).toBeVisible();
    }
    await expect(page.getByTestId('room-management-table')).toBeVisible();
  });

  test('RM-002: 按房间号搜索本次创建的房间', async ({ page }) => {
    const rooms = new RoomManagementPage(page);
    const room = newRoom();
    try {
      await rooms.create(room);
      await rooms.search(room.roomNo);
      await expect(rooms.row(room.roomNo)).toHaveCount(1);
      await expect(rooms.row(room.roomNo).getByRole('cell').nth(2)).toHaveText(String(room.floor));
    } finally {
      await rooms.cleanup(room.roomNo);
    }
  });

  test('RM-003: 重置房间筛选条件', async ({ page }) => {
    const totalText = page.getByText(/共 \d+ 条/);
    const before = await totalText.innerText();

    await page.getByTestId('room-management-search-field-room-no').fill(`不存在-${randomUUID()}`);
    await page.getByTestId('room-management-search-button').click();
    await expect(page.getByRole('row').filter({ hasText: '不存在-' })).toHaveCount(0);

    await page.getByTestId('room-management-reset-button').click();
    await expect(page.getByTestId('room-management-search-field-room-no')).toHaveValue('');
    await expect(totalText).toHaveText(before);
  });

  test('RM-004: 新增房间成功', async ({ page }) => {
    const rooms = new RoomManagementPage(page);
    const room = newRoom();
    try {
      await rooms.create(room);
      const row = rooms.row(room.roomNo);
      await expect(row).toContainText('9');
      await expect(row).toContainText(room.layout);
      await expect(row).toContainText(room.status);
    } finally {
      await rooms.cleanup(room.roomNo);
    }
  });

  test('RM-005: 编辑弹窗回显房间面积', async ({ page }) => {
    const rooms = new RoomManagementPage(page);
    const room = newRoom();
    try {
      await rooms.create(room);
      await rooms.search(room.roomNo);
      await rooms.row(room.roomNo).getByTestId('room-management-edit-button').click();

      const dialog = page.getByRole('dialog', { name: '编辑房间' });
      await expect(dialog.getByTestId('room-management-field-area')).toHaveValue(String(room.area));
    } finally {
      await rooms.cleanup(room.roomNo);
    }
  });

  test('RM-006: 新增房间必填字段校验', async ({ page }) => {
    await page.getByTestId('room-management-create-button').click();
    const dialog = page.getByRole('dialog', { name: '新增房间' });
    await dialog.getByTestId('room-management-modal-ok').click();

    for (const message of ['请选择公寓', '请输入房间号', '请输入楼层', '请选择户型', '请输入面积', '请选择状态']) {
      await expect(dialog.locator('.ant-form-item-explain-error').filter({ hasText: message })).toBeVisible();
    }
  });

  test('RM-007: 删除房间成功', async ({ page }) => {
    const rooms = new RoomManagementPage(page);
    const room = newRoom();
    await rooms.create(room);
    await rooms.deleteByRoomNo(room.roomNo);
  });
});
