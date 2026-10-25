import { expect, type Locator, type Page } from '@playwright/test';

export type RoomForm = {
  roomNo: string;
  floor: number;
  layout: string;
  area: number;
  status: string;
};

/** 房间管理页的查询、创建和清理操作。 */
export class RoomManagementPage {
  constructor(private readonly page: Page) {}

  async open() {
    await this.page.goto('/rooms');
    await expect(this.page.getByRole('columnheader', { name: '房间号' })).toBeVisible();
  }

  row(roomNo: string): Locator {
    return this.page.getByRole('row').filter({ hasText: roomNo });
  }

  async create(room: RoomForm) {
    await this.page.getByTestId('room-management-create-button').click();
    const dialog = this.page.getByRole('dialog', { name: '新增房间' });

    const apartmentSelect = dialog.getByTestId('room-management-field-apartment-id');
    await apartmentSelect.locator('#apartmentId').click();
    // Ant Design 会保留筛选区的隐藏 option；限定在当前展开的可见下拉框。
    const firstApartment = this.page.locator('.ant-select-dropdown:visible .ant-select-item-option').first();
    await expect(firstApartment).toBeVisible();
    await firstApartment.click();

    await dialog.getByTestId('room-management-field-room-no').fill(room.roomNo);
    await dialog.getByTestId('room-management-field-floor').fill(String(room.floor));
    await dialog.getByTestId('room-management-field-layout').click();
    await this.selectVisibleOption(room.layout);
    await dialog.getByTestId('room-management-field-area').fill(String(room.area));
    await dialog.getByTestId('room-management-field-status').click();
    await this.selectVisibleOption(room.status);

    await dialog.getByTestId('room-management-modal-ok').click();
    await expect(this.page.getByText('创建成功', { exact: true })).toBeVisible();
    await expect(this.row(room.roomNo)).toBeVisible();
  }

  private async selectVisibleOption(label: string) {
    // Ant Design 虚拟列表的 role=option 节点尺寸为 0；使用 CLI 探索确认过的可见 option 节点。
    const option = this.page.locator(
      `.ant-select-dropdown:visible .ant-select-item-option[title="${label}"]`,
    );
    await expect(option).toBeVisible();
    await option.click();
  }

  async search(roomNo: string) {
    await this.page.getByTestId('room-management-search-field-room-no').fill(roomNo);
    await this.page.getByTestId('room-management-search-button').click();
  }

  async deleteByRoomNo(roomNo: string) {
    await this.search(roomNo);
    const row = this.row(roomNo);
    await expect(row).toBeVisible();
    await row.getByTestId('room-management-delete-button').click();

    const dialog = this.page.getByRole('dialog', { name: '确认删除该房间？' });
    await dialog.getByRole('button', { name: /确\s*定/ }).click();
    await expect(this.page.getByText('删除成功', { exact: true })).toBeVisible();
    await expect(row).toHaveCount(0);
  }

  async cleanup(roomNo: string) {
    // 用例失败后回到默认页面，再按唯一房间号定位并清理自己的数据。
    await this.open();
    await this.search(roomNo);
    if (await this.row(roomNo).count()) {
      await this.deleteByRoomNo(roomNo);
    }
  }
}
