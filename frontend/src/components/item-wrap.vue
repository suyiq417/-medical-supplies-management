<template>
    <div class="item-wrap">
        <div class="item-header">
            <div class="header-left">
                <div class="header-dot"></div>
                <div class="header-title">{{ title }}</div>
            </div>
            <div class="header-right">
                <slot name="header-right"></slot>
            </div>
        </div>
        <div class="item-content">
            <slot></slot>
        </div>
    </div>
</template>

<script setup lang="ts">
defineProps({
    title: {
        type: String,
        default: ''
    }
});
</script>

<style scoped lang="scss">
.item-wrap {
    width: 100%;
    height: 100%;
    background: rgba(8, 16, 30, 0.7);
    border: 1px solid rgba(0, 180, 220, 0.3);
    border-radius: 4px;
    backdrop-filter: blur(4px);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;

    &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(0, 220, 250, 0.7), transparent);
    }

    &::after {
        content: '';
        position: absolute;
        bottom: 0;
        right: 0;
        width: 40%;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(0, 220, 250, 0.5));
    }
}

.item-header {
    height: 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 15px;
    border-bottom: 1px solid rgba(0, 180, 220, 0.2);
    background: linear-gradient(90deg, rgba(0, 60, 100, 0.3), rgba(0, 30, 60, 0.1));
}

.header-left {
    display: flex;
    align-items: center;
}

.header-dot {
    width: 6px;
    height: 6px;
    background-color: #00fdfa;
    border-radius: 50%;
    margin-right: 8px;
    box-shadow: 0 0 8px rgba(0, 253, 250, 0.8);
}

.header-title {
    font-size: 16px;
    font-weight: 500;
    color: #00fdfa;
    letter-spacing: 1px;
}

.item-content {
    flex: 1;
    padding: 12px;
    overflow: auto;

    &::-webkit-scrollbar {
        width: 4px;
    }

    &::-webkit-scrollbar-thumb {
        background: rgba(0, 180, 220, 0.5);
        border-radius: 2px;
    }

    &::-webkit-scrollbar-track {
        background: rgba(0, 50, 80, 0.1);
        border-radius: 2px;
    }
}
</style>
