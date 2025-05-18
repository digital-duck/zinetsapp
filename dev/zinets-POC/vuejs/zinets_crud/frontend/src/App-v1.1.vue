<!-- App.vue -->
<template>
  <div class="container">
    <el-config-provider>
      <h1>Chinese Character Manager</h1>
      
      <!-- Search Controls -->
      <div class="search-container">
        <el-form :inline="true" class="search-form">
          <el-form-item label="Character">
            <el-input v-model="searchParams.character" placeholder="Character" clearable></el-input>
          </el-form-item>
          <el-form-item label="Meaning">
            <el-input v-model="searchParams.meaning" placeholder="Meaning" clearable></el-input>
          </el-form-item>
          <el-form-item label="Provider">
            <el-select v-model="searchParams.llm_provider" placeholder="Provider" clearable>
              <el-option v-for="provider in providers" :key="provider" :label="provider" :value="provider"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="Active">
            <el-select v-model="searchParams.is_active" placeholder="Status" clearable>
              <el-option label="Active" value="Y"></el-option>
              <el-option label="Inactive" value="N"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchCharacters">Search</el-button>
            <el-button @click="resetSearch">Reset</el-button>
            <el-button type="success" @click="createNewCharacter">New</el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- Upper Panel: Character List -->
      <div class="upper-panel">
        <el-table
          :data="characters"
          style="width: 100%"
          @row-click="handleRowClick"
          v-loading="tableLoading"
        >
          <el-table-column prop="character" label="Character" width="100" sortable></el-table-column>
          <el-table-column prop="pinyin" label="Pinyin" width="120" sortable></el-table-column>
          <el-table-column prop="meaning" label="Meaning" width="250"></el-table-column>
          <el-table-column prop="composition" label="Composition" width="250"></el-table-column>
          <el-table-column prop="phrases" label="Phrases" width="300"></el-table-column>
          <el-table-column prop="llm_provider" label="Provider" width="120" sortable></el-table-column>
          <el-table-column prop="is_active" label="Active" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active === 'Y' ? 'success' : 'danger'">
                {{ row.is_active === 'Y' ? 'Yes' : 'No' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_best" label="Best" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_best === 'Y' ? 'success' : 'info'">
                {{ row.is_best === 'Y' ? 'Yes' : 'No' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next"
            :total="totalCharacters"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
      
      <!-- Lower Panel: Character Details -->
      <div class="lower-panel" v-loading="formLoading">
        <h2>{{ isCreating ? 'Create New Character' : 'Character Details' }}</h2>
        <el-form 
          :model="currentCharacter" 
          label-width="120px"
          :rules="formRules"
          ref="characterForm"
        >
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="Character" prop="character">
                <el-input v-model="currentCharacter.character" :disabled="!isCreating"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Pinyin" prop="pinyin">
                <el-input v-model="currentCharacter.pinyin"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Provider" prop="llm_provider">
                <el-select v-model="currentCharacter.llm_provider" :disabled="!isCreating">
                  <el-option v-for="provider in providers" :key="provider" :label="provider" :value="provider"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Model" prop="llm_model_name">
                <el-input v-model="currentCharacter.llm_model_name" :disabled="!isCreating"></el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Timestamp">
                <el-input v-model="currentCharacter.timestamp" disabled></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="Meaning" prop="meaning">
                <el-input v-model="currentCharacter.meaning" type="textarea" :rows="2"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="Composition" prop="composition">
                <el-input v-model="currentCharacter.composition" type="textarea" :rows="2"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="Phrases" prop="phrases">
                <el-input v-model="currentCharacter.phrases" type="textarea" :rows="3"></el-input>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="Active">
                <el-switch
                  v-model="isActive"
                  active-text="Active"
                  inactive-text="Inactive"
                ></el-switch>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Best">
                <el-switch
                  v-model="isBest"
                  active-text="Best"
                  inactive-text="Not Best"
                ></el-switch>
              </el-form-item>
            </el-col>
          </el-row>
          
          <div class="form-actions">
            <el-button type="primary" @click="saveCharacter" :disabled="!isFormChanged">Save</el-button>
            <el-button @click="cancelEdit">Cancel</el-button>
            <el-button type="danger" @click="confirmDelete" :disabled="isCreating">Delete</el-button>
          </div>
        </el-form>
      </div>
    </el-config-provider>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export default {
  name: 'App',
  setup() {
    // State
    const characters = ref([]);
    const currentCharacter = ref({
      character: '',
      pinyin: '',
      meaning: '',
      composition: '',
      phrases: '',
      llm_provider: '',
      llm_model_name: '',
      timestamp: '',
      is_active: 'Y',
      is_best: 'Y'
    });
    const originalCharacter = ref({});
    const isCreating = ref(false);
    const tableLoading = ref(false);
    const formLoading = ref(false);
    const characterForm = ref(null);
    
    // Pagination
    const currentPage = ref(1);
    const pageSize = ref(10);
    const totalCharacters = ref(0);
    
    // Search params
    const searchParams = reactive({
      character: '',
      meaning: '',
      llm_provider: '',
      is_active: ''
    });
    
    // Providers list (could be fetched from API)
    const providers = ref(['Google', 'OpenAI', 'Anthropic', 'Claude']);
    
    // Form validation rules
    const formRules = {
      character: [{ required: true, message: 'Character is required', trigger: 'blur' }],
      pinyin: [{ required: true, message: 'Pinyin is required', trigger: 'blur' }],
      llm_provider: [{ required: true, message: 'Provider is required', trigger: 'change' }],
      llm_model_name: [{ required: true, message: 'Model name is required', trigger: 'blur' }]
    };
    
    // Computed properties for switches
    const isActive = computed({
      get: () => currentCharacter.value.is_active === 'Y',
      set: (val) => { currentCharacter.value.is_active = val ? 'Y' : 'N'; }
    });
    
    const isBest = computed({
      get: () => currentCharacter.value.is_best === 'Y',
      set: (val) => { currentCharacter.value.is_best = val ? 'Y' : 'N'; }
    });
    
    // Check if form has been changed
    const isFormChanged = computed(() => {
      if (isCreating.value) return true;
      
      return JSON.stringify(currentCharacter.value) !== JSON.stringify(originalCharacter.value);
    });
    
    // Methods
    async function fetchCharacters() {
      tableLoading.value = true;
      
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          ...searchParams
        };
        
        const response = await axios.get(`${API_URL}/characters`, { params });
        characters.value = response.data.items;
        totalCharacters.value = response.data.total;
      } catch (error) {
        ElMessage.error('Failed to fetch characters');
        console.error(error);
      } finally {
        tableLoading.value = false;
      }
    }
    
    function handleRowClick(row) {
      isCreating.value = false;
      formLoading.value = true;
      
      // Clone the row data to currentCharacter
      currentCharacter.value = JSON.parse(JSON.stringify(row));
      originalCharacter.value = JSON.parse(JSON.stringify(row));
      
      formLoading.value = false;
    }
    
    function createNewCharacter() {
      isCreating.value = true;
      currentCharacter.value = {
        character: '',
        pinyin: '',
        meaning: '',
        composition: '',
        phrases: '',
        llm_provider: '',
        llm_model_name: '',
        timestamp: new Date().toISOString(),
        is_active: 'Y',
        is_best: 'Y'
      };
    }
    
    async function saveCharacter() {
      try {
        await characterForm.value.validate();
        
        formLoading.value = true;
        
        if (isCreating.value) {
          // Create new character
          await axios.post(`${API_URL}/characters`, currentCharacter.value);
          ElMessage.success('Character created successfully');
        } else {
          // Update existing character
          await axios.put(
            `${API_URL}/characters/${currentCharacter.value.character}/${currentCharacter.value.llm_provider}/${currentCharacter.value.llm_model_name}`,
            currentCharacter.value
          );
          ElMessage.success('Character updated successfully');
        }
        
        // Refresh data
        fetchCharacters();
        
        // Reset creation mode
        isCreating.value = false;
        
      } catch (error) {
        if (error.response) {
          ElMessage.error(error.response.data.detail || 'Operation failed');
        } else {
          ElMessage.error('Operation failed');
        }
        console.error(error);
      } finally {
        formLoading.value = false;
      }
    }
    
    function cancelEdit() {
      if (isCreating.value) {
        isCreating.value = false;
        currentCharacter.value = JSON.parse(JSON.stringify(originalCharacter.value));
      } else {
        currentCharacter.value = JSON.parse(JSON.stringify(originalCharacter.value));
      }
    }
    
    function confirmDelete() {
      ElMessageBox.confirm(
        'Are you sure you want to deactivate this character?',
        'Warning',
        {
          confirmButtonText: 'Confirm',
          cancelButtonText: 'Cancel',
          type: 'warning',
        }
      )
        .then(() => {
          softDeleteCharacter();
        })
        .catch(() => {
          // User cancelled
        });
    }
    
    async function softDeleteCharacter() {
      try {
        formLoading.value = true;
        
        // Soft delete by setting is_active to 'N'
        const char = currentCharacter.value;
        await axios.patch(
          `${API_URL}/characters/${char.character}/${char.llm_provider}/${char.llm_model_name}/deactivate`
        );
        
        ElMessage.success('Character deactivated successfully');
        
        // Refresh data
        fetchCharacters();
      } catch (error) {
        ElMessage.error('Failed to deactivate character');
        console.error(error);
      } finally {
        formLoading.value = false;
      }
    }
    
    function searchCharacters() {
      currentPage.value = 1;
      fetchCharacters();
    }
    
    function resetSearch() {
      Object.keys(searchParams).forEach(key => {
        searchParams[key] = '';
      });
      currentPage.value = 1;
      fetchCharacters();
    }
    
    function handleSizeChange(size) {
      pageSize.value = size;
      fetchCharacters();
    }
    
    function handleCurrentChange(page) {
      currentPage.value = page;
      fetchCharacters();
    }
    
    // Initial data load
    onMounted(() => {
      fetchCharacters();
    });
    
    return {
      // State
      characters,
      currentCharacter,
      isCreating,
      tableLoading,
      formLoading,
      characterForm,
      searchParams,
      providers,
      formRules,
      isFormChanged,
      
      // Pagination
      currentPage,
      pageSize,
      totalCharacters,
      
      // Methods
      fetchCharacters,
      handleRowClick,
      createNewCharacter,
      saveCharacter,
      cancelEdit,
      confirmDelete,
      searchCharacters,
      resetSearch,
      handleSizeChange,
      handleCurrentChange
    };
  }
}
</script>

<style>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
}

.search-container {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
}

.upper-panel {
  margin-bottom: 20px;
}

.lower-panel {
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.form-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}
</style>
