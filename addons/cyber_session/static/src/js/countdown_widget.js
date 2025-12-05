/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class CountdownWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            countdown: "00:00:00.000"
        });
        this.intervalId = null;
        this.hasClosedSession = false;

        onWillStart(() => {
            this.updateCountdown();
            // Cập nhật mỗi 100ms để hiển thị mili giây
            this.intervalId = setInterval(() => {
                this.updateCountdown();
            }, 100);
        });

        onWillDestroy(() => {
            if (this.intervalId) {
                clearInterval(this.intervalId);
            }
        });
    }

    async updateCountdown() {
        const endTimeExpected = this.props.record.data.end_time_expected;
        const sessionState = this.props.record.data.session_state;

        if (!endTimeExpected || sessionState !== 'running') {
            this.state.countdown = "00:00:00.000";
            return;
        }

        // Chuyển đổi end_time_expected từ string sang Date object
        const endTime = new Date(endTimeExpected);
        const now = new Date();

        // Tính thời gian còn lại (milliseconds)
        const timeDiff = endTime - now;

        if (timeDiff <= 0) {
            this.state.countdown = "00:00:00.000 (Hết giờ)";

            // Tự động đóng phiên ngay khi hết giờ
            if (!this.hasClosedSession) {
                this.hasClosedSession = true;
                if (this.intervalId) {
                    clearInterval(this.intervalId);
                }
                await this.closeSession();
            }
            return;
        }

        // Chuyển đổi sang giờ:phút:giây:mili giây
        const totalSeconds = Math.floor(timeDiff / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        const milliseconds = timeDiff % 1000;

        this.state.countdown = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
    }

    async closeSession() {
        try {
            const sessionId = this.props.record.resId;
            await this.orm.call(
                'cyber.session',
                'action_autoclose_session',
                [sessionId]
            );
            // Reload để cập nhật UI
            if (this.props.record.model.root.load) {
                await this.props.record.model.root.load();
            }
        } catch (error) {
            console.error("Error closing session:", error);
        }
    }
}

CountdownWidget.template = "cyber_session.CountdownWidget";

export const countdownWidget = {
    component: CountdownWidget,
};

registry.category("fields").add("countdown_timer", countdownWidget);
