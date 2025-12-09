<template>
    <div class="not-found">
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for does not exist.</p>
        <router-link to="/">Go to Home</router-link>
        <button @click="goBack">Go Back</button>


    </div>
</template>
<script setup>
const goBack = () => {
    window.history.back();
}
</script>
<style scoped>
.not-found {
    text-align: center;
    padding: 20px;
}
</style>